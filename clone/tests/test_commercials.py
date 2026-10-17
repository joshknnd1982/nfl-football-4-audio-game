"""The player's optional commercials (owner rule 0.14, playbook 7.7.1, game/commercials.py, D-068). This is inspired by Jim Kitchen.

Nothing ships; the setting is off by default; a commercial plays only at the four breaks, after the cue; any key skips it and
is swallowed; the order is a shuffle from the commercials' own generator, so the game's draws are the same with them on or off.
"""
import os
import random

import pytest

from gamerig import Rig
from nfl4.audio.output import SLOT_ONESHOT
from nfl4.data.settingsfile import parse, render
from nfl4.data.settings import Settings
from nfl4.game import extra_texts as words
from nfl4.game.commercials import BREAKS, NOTE_NAME, Commercials
from nfl4.game.keys import KEY_ENTER
from pagrig import Draws, engine_rig, run_steps
from test_game_sounds import ScriptedRnd, plays
from test_pag_breaks import ENTER, F1, F2, break_rig
from wavmaker import write


def make(tmp_path, setting="every", names=("one.wav", "two.wav", "three.wav"), seconds=0.5, rng_seed=3):
    """A rig whose sounds have a commercials folder holding silent wav files of `seconds`."""
    sounds = tmp_path / "sounds"
    sounds.mkdir(parents=True)
    folder = tmp_path / "commercials"
    rig = Rig(sounds_dir=sounds, rng=ScriptedRnd([], seed=1))
    rig.sounds.commercials = Commercials(str(folder), rng=random.Random(rng_seed))
    for name in names:
        write(folder / name, [0.1] * int(11025 * seconds), rate=11025)
    rig.audio_settings.commercials = setting
    spoken = []
    rig.sounds.announce = spoken.append
    return rig, folder, spoken


# ----- the folder and the files -----

def test_the_folder_its_four_break_folders_and_the_note_are_made_and_ship_empty(tmp_path):
    commercials = Commercials(str(tmp_path / "commercials"))
    names = sorted(os.listdir(commercials.folder))
    assert names == sorted(list(BREAKS) + [NOTE_NAME])
    assert commercials.count() == 0 and commercials.choose("quarter") is None


def test_a_deleted_folder_is_made_again_at_the_reload(tmp_path):
    commercials = Commercials(str(tmp_path / "commercials"))
    import shutil
    shutil.rmtree(commercials.folder)
    commercials.refresh()
    assert os.path.isdir(os.path.join(commercials.folder, "halftime")) and os.path.isfile(
        os.path.join(commercials.folder, NOTE_NAME))


def test_a_folder_that_cannot_be_made_does_no_harm(tmp_path):
    blocker = tmp_path / "file"
    blocker.write_text("x")
    commercials = Commercials(str(blocker / "commercials"))              # a path under a file
    assert commercials.choose("final") is None and commercials.count() == 0


def test_files_in_the_folder_play_at_any_break_and_files_in_a_break_folder_only_there(tmp_path):
    commercials = Commercials(str(tmp_path / "commercials"))
    write(tmp_path / "commercials" / "any.wav", [0.1] * 100)
    write(tmp_path / "commercials" / "halftime" / "half.ogg", [0.1] * 100)
    (tmp_path / "commercials" / "notes.txt").write_text("not a sound")
    assert [os.path.basename(p) for p in commercials.candidates("halftime")] == ["any.wav", "half.ogg"]
    assert [os.path.basename(p) for p in commercials.candidates("quarter")] == ["any.wav"]
    assert commercials.count() == 2


def test_every_file_plays_once_before_any_plays_again_and_the_new_bag_does_not_start_with_the_last(tmp_path):
    commercials = Commercials(str(tmp_path / "commercials"), rng=random.Random(11))
    for name in ("a.wav", "b.wav", "c.wav"):
        write(tmp_path / "commercials" / name, [0.1] * 100)
    order = [os.path.basename(commercials.choose("quarter")) for _ in range(12)]
    for start in range(0, 12, 3):
        assert sorted(order[start:start + 3]) == ["a.wav", "b.wav", "c.wav"]
    assert all(order[i] != order[i + 1] for i in range(11))


# ----- the setting -----

def test_the_setting_is_off_by_default_and_saved_in_settings_txt():
    assert Settings.defaults().audio.commercials == "off"
    settings = Settings.defaults()
    settings.audio.commercials = "second"
    again, problems = parse(render(settings))
    assert again.audio.commercials == "second" and problems == []
    bad, problems = parse(render(Settings.defaults()).replace("commercials = off", "commercials = always"))
    assert bad.audio.commercials == "off" and any("commercials" in p for p in problems)


# ----- the break -----

def test_with_the_setting_off_nothing_plays_and_nothing_is_said(tmp_path):
    rig, folder, spoken = make(tmp_path, setting="off")
    t0 = rig.clock()
    rig.sounds.commercial("halftime")
    assert not plays(rig, SLOT_ONESHOT) and spoken == [] and rig.clock() == t0


def test_a_commercial_is_announced_then_played_to_its_end_on_the_one_shot_slot(tmp_path):
    rig, folder, spoken = make(tmp_path, seconds=0.5)
    t0 = rig.clock()
    rig.sounds.commercial("quarter")
    played = plays(rig, SLOT_ONESHOT)
    assert spoken == [words.COMMERCIAL_CUE] and len(played) == 1 and played[0].sound_id.startswith("file ")
    assert rig.clock() - t0 == pytest.approx(0.5, abs=0.01) and rig.keys.code_text == ""


def test_any_key_stops_a_commercial_and_goes_no_further(tmp_path):
    rig, folder, spoken = make(tmp_path, seconds=3.0)
    t0 = rig.clock()
    original_pump = rig.keys.pump
    typed = []

    def pump():
        if not typed and rig.clock() - t0 > 0.4:
            rig.keys.post(KEY_ENTER)
            typed.append(True)
        original_pump()
    rig.keys.pump = pump
    rig.sounds.commercial("final")
    assert rig.clock() - t0 < 0.6 and rig.keys.code_text == ""            # skipped at once, the key is swallowed


def test_every_second_break_plays_on_the_second_and_the_fourth(tmp_path):
    rig, folder, spoken = make(tmp_path, setting="second")
    for _ in range(4):
        rig.sounds.commercial("quarter")
    assert len(plays(rig, SLOT_ONESHOT)) == 2 and len(spoken) == 2


def test_a_folder_with_nothing_usable_means_no_cue_and_no_wait(tmp_path):
    rig, folder, spoken = make(tmp_path, names=())
    t0 = rig.clock()
    rig.sounds.commercial("halftime")
    assert spoken == [] and not plays(rig, SLOT_ONESHOT) and rig.clock() == t0
    (folder / "broken.wav").write_bytes(os.urandom(200))
    rig.sounds.commercial("halftime")
    assert spoken == [] and not plays(rig, SLOT_ONESHOT) and rig.clock() == t0


def test_a_broken_file_is_passed_over_for_a_good_one(tmp_path):
    rig, folder, spoken = make(tmp_path, names=("good.wav",))
    (folder / "aaa broken.wav").write_bytes(os.urandom(200))
    for _ in range(3):
        rig.sounds.commercial("halftime")
    assert len(plays(rig, SLOT_ONESHOT)) >= 1
    assert all(e.sound_id == "file good.wav" for e in plays(rig, SLOT_ONESHOT))


def test_the_games_own_random_numbers_are_not_touched(tmp_path):
    rig, folder, spoken = make(tmp_path)
    for name in BREAKS:
        rig.sounds.commercial(name)
    assert len(plays(rig, SLOT_ONESHOT)) == 4 and rig.rnd.source.drawn == 0


# ----- the places in the game -----

def record_breaks(rig):
    seen = []
    rig.sounds.commercial = seen.append
    return seen


def test_the_end_of_quarters_one_and_three_offer_a_quarter_break_and_quarter_two_a_half_time_break(tmp_path):
    rig = break_rig(tmp_path, [ENTER, ENTER], quarter=1, counter=32)
    seen = record_breaks(rig)
    run_steps(rig, rig.engine.next_play, Draws().rnd(4, 1), until=("offense_menu",))
    assert seen == ["quarter"]
    rig3 = break_rig(tmp_path / "c", [ENTER, ENTER], quarter=3, counter=32)
    seen3 = record_breaks(rig3)
    run_steps(rig3, rig3.engine.next_play, Draws().rnd(4, 1), until=("offense_menu",))
    assert seen3 == ["quarter"]
    rig2 = break_rig(tmp_path / "b", [ENTER, ENTER], quarter=2, counter=32, opening_receiver=1)
    seen2 = record_breaks(rig2)
    d = Draws().raw(0.5)
    for _ in range(15):
        d.raw(0.05).raw(0.9)
    run_steps(rig2, rig2.engine.next_play, d, until=("kick_off",))
    assert seen2 == ["halftime"]


def test_the_two_minute_warning_is_a_break(tmp_path):
    rig = break_rig(tmp_path, [], quarter=2, counter=27)
    seen = record_breaks(rig)
    run_steps(rig, rig.engine.next_play, Draws(), until=("offense_menu",))
    assert seen == ["two-minute-warning"]


def test_the_end_of_the_game_is_a_final_break_after_the_final_score(tmp_path):
    rig = break_rig(tmp_path, [ENTER, ENTER], quarter=4, counter=32)
    rig.engine.s.stats[1].score = 7
    seen = record_breaks(rig)
    run_steps(rig, rig.engine.next_play, Draws(), until=("never",))
    assert seen == ["final"]


def test_a_tie_at_the_end_of_the_fourth_quarter_goes_on_to_overtime_without_a_break(tmp_path):
    rig = break_rig(tmp_path, [ENTER, ENTER], quarter=4, counter=32, wisoff=2, defense=1, half=1)
    seen = record_breaks(rig)
    run_steps(rig, rig.engine.next_play, Draws(), until=("kick_off",))
    assert seen == []
