"""The original's sound procedures on the virtual clock, checked by the slot log. This is inspired by Jim Kitchen.

WAV_EVENT_MAP 4 (every procedure read in the lifted code), GAME_SPEC 7 (dy, the ramps' 0.1 s steps, PlayTackle's
2.5 s, playcel's 0.4 s, PlayRan's 5 s and 3 to 10 s), GAP_REGISTER G-A1 (slots), D-023 (levels, no +1 Hz, c2uh).
"""
import random

import pytest

from gamerig import Rig
from nfl4.audio.output import (EXTRA_SLOT, SLOT_AMBIENT, SLOT_CROWD1, SLOT_CROWD2, SLOT_HIKE, SLOT_NOISE, SLOT_ONESHOT,
                               SLOT_TACKLE)
from nfl4.game.keys import KEY_ENTER


class ScriptedRnd:
    """VB's Rnd from a list (0 <= x < 1), then a seeded generator."""

    def __init__(self, values, seed=5):
        self.values = list(values)
        self.rest = random.Random(seed)
        self.drawn = 0

    def random(self):
        self.drawn += 1
        return self.values.pop(0) if self.values else self.rest.random()


def rnd_for(n, count):
    """A Rnd value whose Int(Rnd * count) is n."""
    return (n + 0.5) / count


def plays(rig, slot=None):
    return [e for e in rig.slot_log if e.action == "play" and (slot is None or e.slot == slot)]


def volumes(rig, slot):
    return [e for e in rig.slot_log if e.action == "volume" and e.slot == slot]


@pytest.fixture
def rig(tmp_path):
    return Rig(sounds_dir=tmp_path / "sounds", rng=random.Random(11))


# ----- the crowd beds -----

def test_start_crowds_loops_both_beds_at_minus_1200_at_their_own_rate(rig):
    rig.sounds.start_crowds()
    one, two = plays(rig)
    assert (one.slot, one.sound_id, one.volume, one.loop, one.freq) == (SLOT_CROWD1, "snd_foot1", -1200, True, 22050)
    assert (two.slot, two.sound_id, two.volume, two.loop, two.freq) == (SLOT_CROWD2, "snd_foot2", -1200, True, 22050)
    assert rig.sounds.crwd1 == -1200
    rig.clock.sleep(3600)
    assert rig.audio.busy(SLOT_CROWD1) and rig.audio.busy(SLOT_CROWD2)


def test_wavol_is_added_to_every_level(tmp_path):
    rig = Rig(sounds_dir=tmp_path, sound_level=-1500)
    s = rig.sounds
    s.start_crowds()
    s.play_hike()
    s.play_tackle(2)
    s.play(7, -1200)
    s.set_crwd1(-100)
    levels = [(e.sound_id, e.volume) for e in plays(rig)]
    assert levels == [("snd_foot1", -2700), ("snd_foot2", -2700), ("snd_foot3", -3100), ("snd_foot14", -4250),
                      ("snd_foot5", -3000), ("snd_foot7", -2700)]
    assert volumes(rig, SLOT_CROWD1)[-1].volume == -1600 and rig.audio.volume(SLOT_CROWD1) == -1600


def test_set_crwd1_raises_crowd_1_for_a_game_without_restarting_it(rig):
    rig.sounds.start_crowds()
    rig.sounds.set_crwd1(-100)
    assert rig.sounds.crwd1 == -100 and rig.audio.volume(SLOT_CROWD1) == -100
    assert len(plays(rig, SLOT_CROWD1)) == 1 and rig.audio.busy(SLOT_CROWD1)


def test_stop_crowds_stops_both_beds(rig):
    rig.sounds.start_crowds()
    rig.sounds.stop_crowds()
    assert not rig.audio.busy(SLOT_CROWD1) and not rig.audio.busy(SLOT_CROWD2)


# ----- the crowd 2 ramps (GAME_SPEC 7: steps of 100 with dy(0.1)) -----

def ramp_steps(rig, mark, start_time):
    """(seconds after start_time, level) of every crowd 2 level change logged after the log held `mark` events."""
    return [(round(e.time - start_time, 2), e.volume) for e in rig.slot_log[mark:]
            if e.action == "volume" and e.slot == SLOT_CROWD2]


def test_c2uf_from_the_base_is_13_steps_in_1_3_seconds(rig):
    rig.sounds.start_crowds()
    mark, t0 = len(rig.slot_log), rig.clock()
    rig.sounds.c2uf()
    steps = ramp_steps(rig, mark, t0)
    assert [v for _, v in steps] == list(range(-1200, 1, 100))
    assert [t for t, _ in steps] == pytest.approx([0.1 * i for i in range(13)], abs=0.015)
    assert rig.clock() - t0 == pytest.approx(1.3, abs=0.02)
    assert rig.audio.volume(SLOT_CROWD2) == 0 and len(plays(rig, SLOT_CROWD2)) == 1      # one loop, never restarted


def test_c2dh_from_full_is_7_steps_to_minus_600_in_0_7_seconds(rig):
    rig.sounds.start_crowds()
    rig.audio.set_volume(SLOT_CROWD2, 0)
    mark, t0 = len(rig.slot_log), rig.clock()
    rig.sounds.c2dh()
    assert [v for _, v in ramp_steps(rig, mark, t0)] == list(range(0, -601, -100))
    assert rig.clock() - t0 == pytest.approx(0.7, abs=0.02)


def test_c2df_goes_down_to_the_base(rig):
    rig.sounds.start_crowds()
    rig.audio.set_volume(SLOT_CROWD2, -600)
    mark, t0 = len(rig.slot_log), rig.clock()
    rig.sounds.c2df()
    assert [v for _, v in ramp_steps(rig, mark, t0)] == list(range(-600, -1201, -100))
    assert rig.audio.volume(SLOT_CROWD2) == -1200


def test_c2uh_never_ramps_and_takes_no_time(rig):
    """D-023 quirk: its end is the current level + wavol - 600, below the start, so the For loop never runs."""
    rig.sounds.start_crowds()
    for level in (-1200, -600, 0):
        rig.audio.set_volume(SLOT_CROWD2, level)
        t0, before = rig.clock(), len(rig.slot_log)
        rig.sounds.c2uh()
        assert rig.clock() == t0 and len(rig.slot_log) == before


def test_a_ramp_already_at_its_end_sets_once_and_waits_once(rig):
    """VB's For v = 0 To 0 runs once: c2uf at full sets 0 and waits 0.1 s; a ramp past its end does nothing."""
    rig.sounds.start_crowds()
    rig.audio.set_volume(SLOT_CROWD2, 0)
    mark, t0 = len(rig.slot_log), rig.clock()
    rig.sounds.c2uf()
    assert [v for _, v in ramp_steps(rig, mark, t0)] == [0] and rig.clock() - t0 == pytest.approx(0.1, abs=0.01)
    rig.audio.set_volume(SLOT_CROWD2, -1200)
    mark, t0 = len(rig.slot_log), rig.clock()
    rig.sounds.c2dh()                                                   # -1200 is already below -600
    assert ramp_steps(rig, mark, t0) == [] and rig.clock() == t0


def test_ramps_follow_wavol(tmp_path):
    rig = Rig(sounds_dir=tmp_path, sound_level=-500)
    rig.sounds.start_crowds()
    mark, t0 = len(rig.slot_log), rig.clock()
    rig.sounds.c2uf()
    rig.sounds.c2dh()
    rig.sounds.c2df()
    values = [v for _, v in ramp_steps(rig, mark, t0)]
    assert values == list(range(-1700, -499, 100)) + list(range(-500, -1101, -100)) + list(range(-1100, -1701, -100))


def test_keys_during_a_ramp_are_kept_and_do_not_shorten_it(tmp_path):
    rig = Rig(sounds_dir=tmp_path)
    rig.sounds.start_crowds()
    rig.keys.post(KEY_ENTER)
    t0 = rig.clock()
    rig.sounds.c2uf()
    assert rig.clock() - t0 == pytest.approx(1.3, abs=0.02) and rig.keys.code_text == str(KEY_ENTER)


# ----- hike, play noise, tackle -----

def test_make_hike_and_make_play_noise_set_levels_and_play_nothing(rig):
    rig.sounds.make_hike()
    rig.sounds.make_play_noise()
    assert plays(rig) == [] and rig.audio.volume(SLOT_HIKE) == -1600 and rig.audio.volume(SLOT_NOISE) == -2750


def test_play_hike_plays_the_hike_once_then_loops_the_play_noise_without_waiting(rig):
    t0 = rig.clock()
    rig.sounds.play_hike()
    hike, noise = plays(rig)
    assert (hike.slot, hike.sound_id, hike.volume, hike.loop) == (SLOT_HIKE, "snd_foot3", -1600, False)
    assert (noise.slot, noise.sound_id, noise.volume, noise.loop) == (SLOT_NOISE, "snd_foot14", -2750, True)
    assert rig.clock() == t0
    rig.clock.sleep(60)
    assert rig.audio.busy(SLOT_NOISE) and not rig.audio.busy(SLOT_HIKE)


def test_the_hike_restarts_from_its_start_at_every_snap(rig):
    rig.sounds.play_hike()
    rig.clock.sleep(1.0)
    rig.sounds.play_hike()
    rig.clock.sleep(3.0)                                               # 3.08 s from the second start
    assert rig.audio.busy(SLOT_HIKE)


@pytest.mark.parametrize("n, file, seconds", [(1, "snd_foot4", 4.3), (2, "snd_foot5", 3.1), (3, "snd_foot6", 2.93),
                                              (8, "snd_foot11", 1.95)])
def test_play_tackle_plays_its_sound_stops_the_noise_and_waits_2_5_seconds(rig, n, file, seconds):
    rig.sounds.play_hike()
    t0 = rig.clock()
    rig.sounds.play_tackle(n)
    tackle = plays(rig, SLOT_TACKLE)[-1]
    assert (tackle.sound_id, tackle.volume, tackle.loop) == (file, -1500, False)
    assert not rig.audio.busy(SLOT_NOISE)
    assert rig.clock() - t0 == pytest.approx(2.5, abs=0.002)           # 2.5 s whatever the sound's length
    assert rig.audio.busy(SLOT_TACKLE) == (seconds > 2.5)


def test_a_second_tackle_within_the_first_ones_length_cuts_it(rig):
    """G-A1: foot4 is 4.3 s; the next PlayTackle comes 2.5 s later and replaces it in the tackle slot."""
    rig.sounds.play_tackle(1)
    rig.sounds.play_tackle(8)
    rig.clock.sleep(1.96)
    assert not rig.audio.busy(SLOT_TACKLE)                              # foot11 ended; foot4 would still run


def test_keys_during_play_tackle_are_kept_and_do_not_shorten_it(rig):
    rig.keys.post(KEY_ENTER)
    t0 = rig.clock()
    rig.sounds.play_tackle(3)
    assert rig.clock() - t0 == pytest.approx(2.5, abs=0.002) and rig.keys.code_text == str(KEY_ENTER)


def test_stop_play_noise_stops_only_the_noise(rig):
    rig.sounds.start_crowds()
    rig.sounds.play_hike()
    rig.sounds.stop_play_noise()
    assert not rig.audio.busy(SLOT_NOISE) and rig.audio.busy(SLOT_CROWD2)


# ----- play and play2 on the one-shot slot -----

def test_play_waits_to_the_end_of_the_sound_and_a_key_does_not_stop_it(rig):
    rig.keys.post(KEY_ENTER)
    rig.keys.pump()                                                     # a key already read: clk throws it away
    t0 = rig.clock()
    rig.sounds.play(7, -1500)
    one = plays(rig, SLOT_ONESHOT)[-1]
    assert (one.sound_id, one.volume, one.freq, one.loop) == ("snd_foot7", -1500, 22050, False)
    assert rig.clock() - t0 == pytest.approx(0.6, abs=0.002)
    assert rig.keys.code_text == "" and not rig.audio.busy(SLOT_ONESHOT)
    assert rig.slot_log[-1].action == "stop" and rig.slot_log[-1].slot == SLOT_ONESHOT


def test_a_key_still_waiting_when_play_starts_survives_clk_as_in_the_original(rig):
    """clk: g = "", DoEvents (Form_KeyDown reads the waiting key: g is set again), g2 = "", DoEvents (GAME_SPEC 8.1)."""
    rig.keys.post(KEY_ENTER)
    rig.sounds.play(12, -1000)
    assert rig.keys.code_text == str(KEY_ENTER)


def test_a_key_typed_during_play_stays_for_the_caller(rig):
    played = []

    def type_during():
        rig.keys.post(KEY_ENTER)
        played.append(rig.clock())
    rig.audio.play(SLOT_CROWD1, "snd_foot1", -1200, loop=True)
    t0 = rig.clock()
    original_pump = rig.keys.pump

    def pump():
        if not played and rig.clock() - t0 > 0.2:
            type_during()
        original_pump()
    rig.keys.pump = pump
    rig.sounds.play(12, -1000)
    assert rig.clock() - t0 == pytest.approx(0.4, abs=0.002) and rig.keys.code_text == str(KEY_ENTER)


def test_a_waited_sound_switched_off_takes_no_time_and_a_silent_file_takes_its_length(tmp_path):
    """G-A3, D-038: "off" plays nothing and waits nothing; a silent wav of the player's plays and is waited."""
    from nfl4.audio.soundsconfig import DEFAULT_TEXT, FILE_NAME
    from wavmaker import write
    player = tmp_path / "sounds"
    player.mkdir()
    (player / FILE_NAME).write_text(DEFAULT_TEXT + "snd_foot25 = off\nfoot15 = off\n", encoding="utf-8")
    write(player / "foot13.wav", [0.0] * 11025, rate=11025)            # one second of silence for the bleep
    rig = Rig(sounds_dir=player, rng=ScriptedRnd([rnd_for(0, 10), rnd_for(30, 40)]))
    t0 = rig.clock()
    rig.sounds.play(25, 0)                                              # the Super Bowl piece, 11.5 s in the original
    assert rig.clock() - t0 < 0.002
    rig.sounds.celebration_sound()                                      # foot15, switched off: draws as usual, no wait
    assert rig.clock() - t0 < 0.004 and rig.rnd.source.drawn == 2       # S7.3a: the rig's generator wraps the scripted source
    rig.sounds.play(13, 0)
    assert rig.clock() - t0 == pytest.approx(1.0, abs=0.006)


def test_play_of_foot2_uses_the_one_shot_slot_beside_the_crowd_bed(rig):
    """The end of an overtime period: play("2", 0) loads foot2 into the one-shot buffer; crowd 2 keeps looping."""
    rig.sounds.start_crowds()
    rig.sounds.play(2, 0)
    assert plays(rig)[-1].slot == SLOT_ONESHOT and rig.audio.busy(SLOT_CROWD2)


def test_play2_plays_at_wavol_and_the_files_own_rate_until_it_ends(tmp_path):
    rig = Rig(sounds_dir=tmp_path, sound_level=-300)
    t0 = rig.clock()
    rig.sounds.play2("foot0")
    one = plays(rig)[-1]
    assert (one.slot, one.sound_id, one.volume, one.freq) == (SLOT_ONESHOT, "snd_foot0", -300, 22050)
    assert rig.clock() - t0 == pytest.approx(3.405, abs=0.002)


def test_play2_stops_at_a_key_and_leaves_it_for_the_caller(rig):
    t0 = rig.clock()
    original_pump = rig.keys.pump

    def pump():
        if rig.clock() - t0 > 0.5 and rig.keys.code_text == "":
            rig.keys.post(KEY_ENTER)
        original_pump()
    rig.keys.pump = pump
    rig.sounds.play2("foot13")                                          # the quit warning's bleep, 0.366 s
    assert rig.clock() - t0 == pytest.approx(0.366, abs=0.002)          # shorter than 0.5 s: no key yet
    t0 = rig.clock()
    rig.sounds.play2("foot0")                                           # 3.4 s
    assert rig.clock() - t0 == pytest.approx(0.501, abs=0.003)
    assert rig.keys.code_text == str(KEY_ENTER) and not rig.audio.busy(SLOT_ONESHOT)


# ----- the celebration -----

def test_celebration_sound_draws_the_file_and_a_nonzero_pitch_step(rig):
    rig.sounds.rng = ScriptedRnd([rnd_for(6, 10), rnd_for(20, 40), rnd_for(23, 40)])   # foot21, k = 0 again, k = 3
    t0 = rig.clock()
    rig.sounds.celebration_sound()
    one = plays(rig)[-1]
    assert (one.slot, one.sound_id, one.volume, one.freq) == (SLOT_ONESHOT, "snd_foot21", -300, 44100 + 300)
    assert rig.sounds.rng.drawn == 3
    assert rig.clock() - t0 == pytest.approx(0.087 * 44100 / 44400, abs=0.002)    # waited to its end


def test_celebration_pitch_has_an_8000_hz_floor(rig):
    rig.sounds.rng = ScriptedRnd([rnd_for(4, 10), rnd_for(0, 40)])                 # foot19 (8,363 Hz), k = -20
    rig.sounds.celebration_sound()
    assert plays(rig)[-1].sound_id == "snd_foot19" and plays(rig)[-1].freq == 8000
    rig.sounds.rng = ScriptedRnd([rnd_for(0, 10), rnd_for(39, 40)])                # foot15 (44,100 Hz), k = 19
    rig.sounds.celebration_sound()
    assert plays(rig)[-1].sound_id == "snd_foot15" and plays(rig)[-1].freq == 46000


def test_celebration_pitches_cover_every_step_but_zero(rig):
    rig.sounds.rng = random.Random(3)
    steps = set()
    for _ in range(600):
        rig.sounds.celebration_sound()
        one = plays(rig)[-1]
        rate = rig.audio.rate(one.sound_id)
        if rate + 100 * -20 >= 8000:
            steps.add((one.freq - rate) // 100)
    assert steps == set(range(-20, 20)) - {0}


def test_playcel_order_and_times(rig):
    """c2uf, 8 to 15 sounds, 0.4 s, foot12 at -500 + wavol, c2df (WAV_EVENT_MAP 4)."""
    rig.sounds.start_crowds()
    rig.sounds.rng = ScriptedRnd([rnd_for(2, 8)] + [rnd_for(0, 10), rnd_for(30, 40)] * 10)   # 10 sounds: foot15, k=10
    t0 = rig.clock()
    rig.sounds.playcel()
    after = [e for e in rig.slot_log if e.time >= t0]
    ups = [e for e in after if e.action == "volume" and e.volume <= 0][:13]
    assert [e.volume for e in ups] == list(range(-1200, 1, 100))
    celebration = [e for e in after if e.action == "play" and e.sound_id == "snd_foot15"]
    assert len(celebration) == 10 and all(e.freq == 45100 and e.volume == -300 for e in celebration)
    contact = [e for e in after if e.action == "play" and e.sound_id == "snd_foot12"]
    assert len(contact) == 1 and contact[0].volume == -500
    gap = contact[0].time - (celebration[-1].time + 0.127 * 44100 / 45100)
    assert gap == pytest.approx(0.4, abs=0.004)
    downs = [e.volume for e in after if e.action == "volume" and e.time > contact[0].time]
    assert downs == list(range(0, -1201, -100))
    assert rig.audio.volume(SLOT_CROWD2) == -1200


def test_playcel_plays_8_to_15_sounds(rig):
    rig.sounds.start_crowds()
    counts = set()
    rig.sounds.rng = random.Random(9)
    for _ in range(60):
        before = len(plays(rig))
        rig.sounds.playcel()
        counts.add(sum(1 for e in plays(rig)[before:] if e.sound_id in {f"snd_foot{n}" for n in range(15, 25)}))
    assert counts == set(range(8, 16))


# ----- the ambient sounds while getkey2 waits -----

def test_no_ambient_sound_in_the_first_5_seconds_of_a_wait(tmp_path):
    rig = Rig(answers=[("wait", 4.9), KEY_ENTER], sounds_dir=tmp_path, rng=random.Random(1))
    rig.keys.getkey2(rig.speech, rig.sounds)
    assert plays(rig, SLOT_AMBIENT) == []


def test_ambient_sounds_start_after_5_seconds_then_every_3_to_10_seconds_after_the_previous_ended(tmp_path):
    rig = Rig(answers=[("wait", 300), KEY_ENTER], sounds_dir=tmp_path, rng=random.Random(2))
    t0 = rig.clock()
    rig.keys.getkey2(rig.speech, rig.sounds)
    ambient = plays(rig, SLOT_AMBIENT)
    assert ambient[0].time - t0 == pytest.approx(5.0, abs=0.002)
    lengths = {"snd_foot8": 1.4, "snd_foot9": 1.5, "snd_foot10": 2.162}
    for before, after in zip(ambient, ambient[1:]):
        gap = after.time - before.time
        assert gap >= lengths[before.sound_id] - 0.002                   # never while the previous one plays
        assert gap <= max(10.0, lengths[before.sound_id]) + 0.003
        assert gap >= 3.0 - 0.002
    assert len(ambient) > 20 and {e.sound_id for e in ambient} == set(lengths)


def test_ambient_levels_and_pans(tmp_path):
    rig = Rig(answers=[("wait", 400), KEY_ENTER], sounds_dir=tmp_path, rng=random.Random(4), sound_level=-200)
    rig.keys.getkey2(rig.speech, rig.sounds)
    pans = set()
    for e in plays(rig, SLOT_AMBIENT):
        if e.sound_id == "snd_foot8":
            assert (e.volume, e.pan) == (-250 - 200, 0)
        elif e.sound_id == "snd_foot9":
            assert (e.volume, e.pan) == (-1200 - 200, 0)
        else:
            assert e.volume == -2900 + abs(e.pan) - 200 and e.pan % 100 == 0
            pans.add(e.pan)
        assert e.freq == rig.audio.rate(e.sound_id) and not e.loop
    assert pans <= set(range(-1500, 1401, 100)) and len(pans) >= 5      # the extremes: test_ambient_sound_choice_draws


def test_ambient_sound_choice_draws(tmp_path):
    rig = Rig(sounds_dir=tmp_path)
    rig.sounds.st4 = 0
    rig.sounds.rng = ScriptedRnd([rnd_for(2, 3), rnd_for(29, 30), 0.0])         # foot10, pan +1400, then 3 s
    rig.sounds.play_ran()
    one = plays(rig)[-1]
    assert (one.sound_id, one.pan, one.volume) == ("snd_foot10", 1400, -1500)
    assert rig.sounds.st4 == pytest.approx(rig.clock() + 3.0)
    rig.audio.stop(SLOT_AMBIENT)
    rig.sounds.st4 = 0
    rig.sounds.rng = ScriptedRnd([rnd_for(2, 3), rnd_for(0, 30), 0.999999])     # pan -1500, then almost 10 s
    rig.sounds.play_ran()
    assert (plays(rig)[-1].pan, plays(rig)[-1].volume) == (-1500, -1400)
    assert rig.sounds.st4 == pytest.approx(rig.clock() + 10.0, abs=1e-4)


def test_getkey2_ends_at_a_key_and_stops_the_speech(tmp_path):
    rig = Rig(answers=[("wait", 1.0), KEY_ENTER], sounds_dir=tmp_path)
    t0 = rig.clock()
    rig.keys.getkey2(rig.speech, rig.sounds)
    assert rig.keys.code_text == str(KEY_ENTER) and rig.clock() - t0 == pytest.approx(1.0, abs=0.003)


def test_load_ambient_stops_the_ambient_slot(rig):
    rig.audio.play(SLOT_AMBIENT, "snd_foot9", -1200)
    rig.sounds.load_ambient()
    assert not rig.audio.busy(SLOT_AMBIENT)


# ----- start-up, the voice choice, the exit -----

def test_intro_plays_foot0_once_waited_then_loops_it_at_the_same_level(tmp_path):
    rig = Rig(sounds_dir=tmp_path, sound_level=-400)
    t0 = rig.clock()
    rig.sounds.intro()
    first, loop = plays(rig)
    assert (first.sound_id, first.volume, first.loop) == ("snd_foot0", -400, False)
    assert (loop.sound_id, loop.volume, loop.loop) == ("snd_foot0", -400, True)
    assert loop.time - t0 == pytest.approx(3.405, abs=0.002)
    rig.clock.sleep(30)
    assert rig.audio.busy(SLOT_ONESHOT)
    rig.sounds.stop_oneshot()
    assert not rig.audio.busy(SLOT_ONESHOT)


def test_loop_foot0_for_the_voice_choice(rig):
    rig.sounds.loop_foot0()
    one = plays(rig)[-1]
    assert (one.slot, one.sound_id, one.volume, one.loop) == (SLOT_ONESHOT, "snd_foot0", 0, True)


def test_stop_all_stops_every_slot(rig):
    rig.sounds.start_crowds()
    rig.sounds.play_hike()
    rig.audio.preview("snd_foot7")
    rig.sounds.stop_all()
    assert not any(rig.audio.busy(slot) for slot in range(8))


def test_no_procedure_uses_the_extra_channel(rig):
    """G-A1: the extra channel is never used in play."""
    s = rig.sounds
    s.start_crowds()
    s.intro()
    s.loop_foot0()
    s.stop_oneshot()
    s.make_hike()
    s.make_play_noise()
    s.play_hike()
    s.play_tackle(1)
    s.play(12, -1000)
    s.play2("foot13")
    s.playcel()
    s.load_ambient()
    s.st4 = 0
    s.play_ran()
    s.c2uh()
    s.set_crwd1(-100)
    s.stop_crowds()
    assert all(e.slot != EXTRA_SLOT for e in rig.slot_log)
    assert {e.slot for e in plays(rig)} == {SLOT_ONESHOT, SLOT_CROWD1, SLOT_CROWD2, SLOT_HIKE, SLOT_AMBIENT,
                                             SLOT_TACKLE, SLOT_NOISE}
