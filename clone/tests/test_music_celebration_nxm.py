"""NX-M1 and NX-M2 (the owner 2026-10-24, D-148, CLAUDE.md 0.31): in the owner's own mode (the N. F. L. rules) the original's music (foot0) and
its touchdown celebration sounds (foot15 to foot24, playcel's closing foot12) are not played. The slots `music` and `celebration` play the player's
file (the sounds folder), else a developer's file of that name in the program's sounds_nx, else nothing, and the random draws are the same either way.
Classic keeps the original's sounds. This is inspired by Jim Kitchen.
"""
import random
import shutil
from pathlib import Path

import pytest

from gamerig import Rig
from nfl4.audio.output import SLOT_ONESHOT

ORIGINAL_MUSIC = {"snd_foot0"}
ORIGINAL_CELEBRATION = {"snd_foot%d" % n for n in range(15, 25)} | {"snd_foot12"}
A_WAV = Path(__file__).resolve().parents[1] / "assets" / "sounds_nx" / "whistle.wav"


class CountingRnd:
    def __init__(self, seed):
        self.inner = random.Random(seed)
        self.drawn = 0

    def random(self):
        self.drawn += 1
        return self.inner.random()


def own_rig(tmp_path, own=True, files=None, seed=11):
    rig = Rig(sounds_dir=tmp_path / "sounds", rng=CountingRnd(seed))
    rig.sounds.own_mode = lambda: own
    slots = files or {}
    rig.sounds.slot_files = lambda name: list(slots.get(name, []))
    return rig


def played(rig):
    return [e for e in rig.slot_log if e.action == "play"]


def ids(rig):
    return {e.sound_id for e in played(rig)}


def a_file(tmp_path, name):
    target = tmp_path / "files" / name
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(A_WAV, target)
    return str(target)


# ----- nothing of the original's music or celebration in the owner's mode -----

def test_the_intro_the_exit_and_the_halftime_play_no_music(tmp_path):
    rig = own_rig(tmp_path)
    rig.sounds.intro()
    rig.sounds.play(0, 0)
    rig.sounds.halftime()
    rig.sounds.loop_foot0()
    assert not ids(rig) & ORIGINAL_MUSIC and not ids(rig) & ORIGINAL_CELEBRATION
    assert not rig.audio.busy(SLOT_ONESHOT)


def test_a_touchdown_has_no_celebration_and_no_closing_contact_sound(tmp_path):
    rig = own_rig(tmp_path)
    rig.sounds.start_crowds()
    for _ in range(5):
        rig.sounds.playcel()
    assert not ids(rig) & ORIGINAL_CELEBRATION


def test_the_volume_demo_is_not_the_original_music(tmp_path):
    rig = own_rig(tmp_path)
    rig.sounds.play2("foot0")
    assert not ids(rig) & ORIGINAL_MUSIC


# ----- the slots -----

def test_the_music_file_plays_at_the_start_looped_and_at_the_exit(tmp_path):
    music = a_file(tmp_path, "music.wav")
    rig = own_rig(tmp_path, files={"music": [music]})
    rig.sounds.intro()
    first = played(rig)[-1]
    assert first.slot == SLOT_ONESHOT and first.loop is True and not ids(rig) & ORIGINAL_MUSIC
    rig.clock.sleep(30)
    assert rig.audio.busy(SLOT_ONESHOT)                     # it loops until the welcome stops it (rule 0.21)
    rig.sounds.stop_oneshot()
    before = len(played(rig))
    rig.sounds.play(0, 0)                                   # the exit and the halftime show
    assert len(played(rig)) == before + 1 and played(rig)[-1].loop is False


def test_the_celebration_files_play_at_a_touchdown(tmp_path):
    cheer = a_file(tmp_path, "celebration1.wav")
    rig = own_rig(tmp_path, files={"celebration": [cheer]})
    rig.sounds.start_crowds()
    before = len(played(rig))
    rig.sounds.playcel()
    run = [e for e in played(rig)[before:] if e.slot == SLOT_ONESHOT]
    assert 8 <= len(run) <= 15 and not {e.sound_id for e in run} & ORIGINAL_CELEBRATION


# ----- the same draws, so a seeded game is the same game -----

@pytest.mark.parametrize("seed", [1, 7, 11, 23])
def test_the_draws_are_the_same_with_and_without_the_files_and_in_classic(tmp_path, seed):
    counts = []
    for own, files in ((False, None), (True, None), (True, {"celebration": [a_file(tmp_path, "celebration1.wav")],
                                                           "music": [a_file(tmp_path, "music.wav")]})):
        rig = own_rig(tmp_path / str(len(counts)), own=own, files=files, seed=seed)
        rig.sounds.start_crowds()
        rig.sounds.playcel()
        rig.sounds.halftime()
        rig.sounds.celebration_run()
        counts.append(rig.rnd.source.drawn)
    assert counts[0] == counts[1] == counts[2]


def test_classic_keeps_the_original_sounds(tmp_path):
    rig = own_rig(tmp_path, own=False)
    rig.sounds.intro()
    rig.sounds.stop_oneshot()
    rig.sounds.start_crowds()
    rig.sounds.playcel()
    assert "snd_foot0" in ids(rig) and "snd_foot12" in ids(rig) and ids(rig) & (ORIGINAL_CELEBRATION - {"snd_foot12"})


def test_the_game_and_the_program_say_the_owners_mode_is_the_nfl_rules(tmp_path):
    from test_functions import rig_for
    rig = rig_for(tmp_path, [])
    game = rig.game
    if game.sounds is None:
        pytest.skip("this rig has no sounds")
    game.options.settings.game.rules = "classic"
    assert game.sounds.own_mode() is False
    game.options.settings.game.rules = "nfl"
    assert game.sounds.own_mode() is True


def test_the_log_names_what_the_start_plays(tmp_path):
    """Rule 0.15: the start's loop_start and loop_stop lines say what plays (NX-M1), so a player's report shows it."""
    music = a_file(tmp_path, "music.wav")
    assert own_rig(tmp_path, own=False).sounds.intro_name() == "intro foot0"
    assert own_rig(tmp_path).sounds.intro_name() == "music slot empty (no file, nothing plays)"
    assert own_rig(tmp_path, files={"music": [music]}).sounds.intro_name() == "music music.wav"
