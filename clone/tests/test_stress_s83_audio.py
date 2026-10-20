"""The sound stress tests of S8.3 (P8; GAP_REGISTER G-A4 and G-A6). This is inspired by Jim Kitchen.

A sound device that is missing at the start or lost in the middle of a game, a sound file damaged in every way a player or a disk can
damage one (playbook 7.10), the folders of the sounds replaced by files or locked, thousands of added files. Whatever happens the game plays
to its end, the pacing of its waits stays, the player hears one short notice, and nothing is kept in memory that should not be.
"""
import os
import random
import struct
import time

import pytest

import nfl4.audio.engine as engine_module
from filedamage import holding, read_only
from gamerig import Rig
from nfl4.audio.engine import DEVICE_LOST_AFTER, DEVICE_LOST_NOTICE, NO_SOUND_NOTICE, Audio
from nfl4.audio.ids import SOUND_IDS
from nfl4.audio.library import SOUND_FILE_NOTICE, SoundLibrary, shipped_sounds_dir
from nfl4.audio.output import SLOT_ONESHOT, OutputError, TimedOutput
from nfl4.data.settings import AudioSettings
from pagrig import make_rig, play
from test_pag_games import lively_policy
from wavmaker import sine, wav_bytes, write


class DyingOutput(TimedOutput):
    """A mixer that works for `plays` plays and then refuses every call, as one whose device was unplugged."""

    def __init__(self, clock, plays):
        super().__init__(clock)
        self.plays_left = plays
        self.dead = False

    def play(self, slot, pcm, gain, loop=False):
        if self.dead or self.plays_left <= 0:
            self.dead = True
            raise OutputError("the device was removed")
        self.plays_left -= 1
        super().play(slot, pcm, gain, loop)

    def _dead(self):
        if self.dead:
            raise OutputError("the device was removed")

    def busy(self, slot):
        self._dead()
        return super().busy(slot)

    def set_gain(self, slot, gain):
        self._dead()
        super().set_gain(slot, gain)

    def stop(self, slot):
        self._dead()
        super().stop(slot)

    def stop_all(self):
        self._dead()
        super().stop_all()


def game_with_output(tmp_path, seed, output_for):
    rig = make_rig(tmp_path, rng=random.Random(seed), fast=True, vtrnt=1 + seed % 2)
    if output_for is not None:
        rig.audio.output = output_for(rig.clock)
    rig.keys.policy = lively_policy(rig, seed + 1000)
    started = rig.clock()
    result = play(rig)
    return rig, result, rig.clock() - started


@pytest.mark.parametrize("seed", range(4))
def test_the_sound_device_lost_in_the_middle_of_a_game_gives_a_silent_game_with_the_same_waits_and_one_notice(tmp_path, seed):
    _, control, normal_seconds = game_with_output(tmp_path / "a", seed, None)
    rig, result, seconds = game_with_output(tmp_path / "b", seed, lambda clock: DyingOutput(clock, 60))
    assert result.scores is not None and result.scores[0] != result.scores[1]
    assert not rig.audio.ok and isinstance(rig.audio.output, TimedOutput) and not isinstance(rig.audio.output, DyingOutput)
    assert rig.audio.take_notices() == [DEVICE_LOST_NOTICE] and rig.audio.take_notices() == []
    assert seconds > 0.6 * normal_seconds, (seconds, normal_seconds)        # the game still takes the time of its sounds
    assert rig.audio.output.played == []                                      # and the silent output keeps no sound in memory


def test_one_refused_play_is_one_bad_sound_and_not_a_lost_device(tmp_path):
    class Once(TimedOutput):
        refused = 0

        def play(self, slot, pcm, gain, loop=False):
            if self.refused < DEVICE_LOST_AFTER - 1:
                self.refused += 1
                raise OutputError("a bad sound")
            super().play(slot, pcm, gain, loop)
    rig = Rig(sounds_dir=tmp_path / "sounds")
    rig.audio.output = Once(rig.clock)
    assert rig.audio.play(SLOT_ONESHOT, "snd_foot12") == 0.0 and rig.audio.play(SLOT_ONESHOT, "snd_foot12") == 0.0
    assert rig.audio.play(SLOT_ONESHOT, "snd_foot12") > 0 and rig.audio.ok and rig.audio.take_notices() == []


def test_a_device_that_is_missing_at_the_start_keeps_nothing_in_memory_however_many_sounds_play(tmp_path, monkeypatch):
    def refuse(*args, **kwargs):
        raise OutputError("no sound device")
    monkeypatch.setattr(engine_module, "PygameOutput", refuse)
    library = SoundLibrary(shipped_sounds_dir(), str(tmp_path / "sounds"))
    audio = Audio(library, AudioSettings(sound_level=0))
    assert not audio.ok and audio.take_notices() == [NO_SOUND_NOTICE]
    for _ in range(300):
        assert audio.play(SLOT_ONESHOT, "snd_foot12") > 0
    assert audio.output.played == []


# ----- damaged sound files -----

def damaged_wavs():
    good = wav_bytes(sine(440, 0.05, 11025), rate=11025)
    rng = random.Random(3)
    return {
        "empty": b"",
        "one_byte": b"R",
        "header_only": good[:12],
        "cut_in_the_fmt_chunk": good[:30],
        "cut_in_the_data": good[:60],
        "random_bytes": bytes(rng.randrange(256) for _ in range(4000)),
        "text": b"this is not a sound file at all\r\n" * 50,
        "zeros": b"\x00" * 3000,
        "data_size_lies_huge": wav_bytes(sine(440, 0.05, 11025), rate=11025, data_size=0xFFFFFFF0),
        "data_size_zero": wav_bytes(sine(440, 0.05, 11025), rate=11025, data_size=0),
        "eight_bit": wav_bytes(sine(440, 0.05, 11025), rate=11025, bits=8),
        "twenty_four_bit": wav_bytes(sine(440, 0.05, 11025), rate=11025, bits=24),
        "float": wav_bytes(sine(440, 0.05, 11025), rate=11025, bits=32, fmt_tag=3),
        "adpcm_tag": wav_bytes(sine(440, 0.05, 11025), rate=11025, fmt_tag=2),
        "rate_zero": wav_bytes(sine(440, 0.05, 11025), rate=0),
        "rate_huge": wav_bytes(sine(440, 0.05, 11025), rate=0x7FFFFFFF),
        "eight_channels": wav_bytes(sine(440, 0.05, 11025), rate=11025, channels=8),
        "riff_without_wave": b"RIFF" + struct.pack("<I", 4) + b"AVI ",
        "chunk_size_past_the_end": good[:36] + b"data" + struct.pack("<I", 8) + b"\x01\x02",
        "a_huge_file": good + b"\x00" * (9 * 1024 * 1024),
    }


@pytest.mark.parametrize("kind", sorted(damaged_wavs()))
def test_every_sound_damaged_in_every_way_falls_back_plays_something_or_nothing_and_says_one_notice(tmp_path, kind):
    data = damaged_wavs()[kind]
    folder = tmp_path / "sounds"
    folder.mkdir()
    for sound_id in SOUND_IDS:
        name = "beep_exit" if sound_id == "beep_exit" else sound_id[4:]
        (folder / (name + ".wav")).write_bytes(data)
    library = SoundLibrary(shipped_sounds_dir(), str(folder))
    audio = Audio(library, AudioSettings(sound_level=0), output=TimedOutput(time.monotonic, keep=False), beeper=type("B", (), {"beep": lambda self: True})())
    for sound_id in SOUND_IDS:
        seconds = audio.play(SLOT_ONESHOT, sound_id)
        assert seconds >= 0.0
        pick = library.pick(sound_id)
        assert pick.source in ("player", "original", "generated", "off", "none")
    problems = library.check_all()
    notices = audio.take_notices()
    assert len(notices) <= 1 and all(SOUND_FILE_NOTICE.strip() in n for n in notices)
    assert isinstance(problems, list)


def test_a_sounds_folder_that_is_a_file_and_a_sounds_txt_that_is_a_folder_do_not_stop_the_start(tmp_path):
    player = tmp_path / "sounds"
    player.write_bytes(b"i am a file where the folder should be")
    library = SoundLibrary(shipped_sounds_dir(), str(player))
    audio = Audio(library, AudioSettings(sound_level=0), output=TimedOutput(time.monotonic, keep=False))
    assert audio.play(SLOT_ONESHOT, "snd_foot12") > 0
    player.unlink()
    player.mkdir()
    (player / "sounds.txt").mkdir()
    library = SoundLibrary(shipped_sounds_dir(), str(player))
    audio = Audio(library, AudioSettings(sound_level=0), output=TimedOutput(time.monotonic, keep=False))
    assert audio.play(SLOT_ONESHOT, "snd_foot12") > 0


def test_a_sound_file_held_open_by_another_program_and_a_read_only_one_fall_back_to_the_original(tmp_path):
    folder = tmp_path / "sounds"
    folder.mkdir()
    path = folder / "foot3.wav"
    path.write_bytes(wav_bytes(sine(300, 0.2, 11025), rate=11025))
    library = SoundLibrary(shipped_sounds_dir(), str(folder))
    audio = Audio(library, AudioSettings(sound_level=0), output=TimedOutput(time.monotonic, keep=False))
    with holding(path):
        library.refresh()
        assert audio.play(SLOT_ONESHOT, "snd_foot3") > 0
    with read_only(path):
        library.refresh()
        assert audio.play(SLOT_ONESHOT, "snd_foot3") > 0 and library.pick("snd_foot3").source == "player"


def test_the_folder_deleted_in_the_middle_of_a_game_is_made_again_at_the_next_refresh(tmp_path):
    folder = tmp_path / "sounds"
    library = SoundLibrary(shipped_sounds_dir(), str(folder))
    audio = Audio(library, AudioSettings(sound_level=0), output=TimedOutput(time.monotonic, keep=False))
    import shutil
    shutil.rmtree(folder)
    assert audio.play(SLOT_ONESHOT, "snd_foot12") > 0
    audio.refresh()
    assert folder.is_dir() and audio.play(SLOT_ONESHOT, "snd_foot12") > 0


def test_three_thousand_added_files_are_scanned_and_drawn_among_quickly(tmp_path):
    folder = tmp_path / "sounds"
    folder.mkdir()
    one = wav_bytes(sine(500, 0.02, 11025), rate=11025)
    for number in range(25, 3025):
        (folder / f"celebration{number}.wav").write_bytes(one)
    started = time.monotonic()
    library = SoundLibrary(shipped_sounds_dir(), str(folder))
    members = library.pool_members("celebration")
    assert len(members) == 10 + 3000 and time.monotonic() - started < 20
    audio = Audio(library, AudioSettings(sound_level=0), output=TimedOutput(time.monotonic, keep=False))
    for member in random.Random(1).sample(members, 200):
        assert audio.play_member(SLOT_ONESHOT, member) > 0
