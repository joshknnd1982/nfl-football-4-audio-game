"""The player's own sound files for the stadium, the referee's microphone and the whistles (nfl4 only, rule 0.13; SZ.2, D-107). This is inspired by Jim Kitchen.

The owner (2026-10-22), after hearing them: "those are good, ensure the user can customize them by adding custom wav files." A file with the
same name in the player's sounds folder replaces the shipped sound, a new number adds one (rule 0.14), the sound layer's formats are read, a file
that cannot be used never leaves a silence where a sound belongs, F9 Sounds lists the nineteen sounds with the file name each takes (and plays them),
the check reads the player's files, and a menu item moves them aside so the originals play again.
"""
import os
import types

import pytest

from nfl4.extras import nx_texts as X
from nfl4.extras import stadium as ST
from nfl4.extras import stadium_menu as SM
from nfl4.extras.nfl_rules import NflRules
from nfl4.game import extra_texts as words
from programrig import DOWN, ENTER, ESC
from test_functions import END, rig_for, sounds_menu


# ----- the nineteen sounds -----

def test_every_sound_a_player_can_replace_is_shipped_has_a_plain_name_and_a_label_in_the_text_table():
    assert len(ST.ALL_NAMES) == 19 and len(set(ST.ALL_NAMES)) == 19
    for name in ST.ALL_NAMES:
        assert os.path.exists(os.path.join(ST.shipped_folder(), name + ".wav")), name
        text = X.TEXTS[ST.LABEL_IDS[name]]
        assert 1 <= len(text.split()) <= 6 and text == text.strip(), name
    assert len({X.TEXTS[i] for i in ST.LABEL_IDS.values()}) == 19
    assert ST.ALL_NAMES[0] == "crowd_cheer" and ST.ALL_NAMES[-1] == "whistle_triple" and ST.LABEL_IDS["mic_on"] == "NXB-S14"


def test_a_family_reads_the_formats_of_the_sound_layer_the_wav_first_and_a_new_number_adds(tmp_path):
    shipped, mine = tmp_path / "shipped", tmp_path / "mine"
    shipped.mkdir()
    mine.mkdir()
    (shipped / "crowd_cheer.wav").write_bytes(b"x")
    for n in ("crowd_cheer.ogg", "crowd_cheer2.mp3", "crowd_cheer2.wav", "crowd_cheer3.flac", "Crowd_Cheer07.WAV", "crowd_cheer.txt", "crowd_roar.wav"):
        (mine / n).write_bytes(b"y")
    files = ST.family("crowd_cheer", (str(mine), str(shipped)))
    assert [os.path.basename(f) for f in files] == ["crowd_cheer.ogg", "crowd_cheer2.wav", "crowd_cheer3.flac", "Crowd_Cheer07.WAV"]
    assert ST.mine(files, str(mine)) == files and ST.mine(files, str(shipped)) == []


# ----- a file that cannot be used -----

class FakeLibrary:
    def __init__(self, bad=()):
        self.bad, self.asked = tuple(bad), []

    def pick_file(self, path):
        self.asked.append(path)
        return types.SimpleNamespace(sound=None if any(b in path for b in self.bad) else object())


def stadium_with(tmp_path, library):
    st = ST.Stadium(NflRules(), on=True)
    st.folders = (str(tmp_path / "mine"), str(tmp_path / "shipped"))
    st.game = types.SimpleNamespace(sounds=types.SimpleNamespace(audio=types.SimpleNamespace(library=library)))
    return st


def test_a_damaged_file_of_the_player_is_skipped_and_the_shipped_sound_plays_instead(tmp_path):
    (tmp_path / "mine").mkdir()
    (tmp_path / "shipped").mkdir()
    (tmp_path / "shipped" / "crowd_cheer.wav").write_bytes(b"x")
    (tmp_path / "mine" / "crowd_cheer.wav").write_bytes(b"bad")
    st = stadium_with(tmp_path, FakeLibrary(bad=(os.sep + "mine" + os.sep + "crowd_cheer.wav",)))
    assert [os.path.basename(os.path.dirname(f)) for f in st.files("crowd_cheer")] == ["shipped"]
    (tmp_path / "mine" / "crowd_cheer2.wav").write_bytes(b"good-enough")                # a second, good file joins the family
    assert [os.path.basename(f) for f in st.files("crowd_cheer")] == ["crowd_cheer2.wav"]


def test_the_check_counts_the_players_files_it_cannot_read(tmp_path):
    mine = tmp_path / "mine"
    mine.mkdir()
    for n in ("crowd_boo.wav", "whistle_long2.wav", "mic_on.ogg", "foot7.wav", "crowd_boo_extra.wav"):
        (mine / n).write_bytes(b"?")
    library = FakeLibrary(bad=("mic_on", "whistle_long2"))
    assert ST.check_files(library, str(mine)) == 2
    assert len(library.asked) == 3                                                  # foot7 and the unrelated name are not the stadium's


# ----- put the sounds back -----

def test_put_back_moves_only_the_stadium_files_aside_and_never_deletes(tmp_path):
    mine = tmp_path / "sounds"
    mine.mkdir()
    for n in ("crowd_cheer.wav", "crowd_cheer2.mp3", "whistle_long.ogg", "mic_off.wav", "foot7.wav", "my_laugh.wav", "crowd_cheer_old.wav"):
        (mine / n).write_bytes(b"y")
    result = ST.put_back(str(mine))
    assert sorted(result.moved) == ["crowd_cheer.wav", "crowd_cheer2.mp3", "mic_off.wav", "whistle_long.ogg"]
    assert sorted(os.listdir(mine / "removed sounds")) == sorted(result.moved)
    assert sorted(n for n in os.listdir(mine) if n != "removed sounds") == ["crowd_cheer_old.wav", "foot7.wav", "my_laugh.wav"]
    assert ST.put_back(str(mine)).moved == [] and ST.put_back(str(tmp_path / "nothing")).moved == []


# ----- the list in F9, Sounds -----

def test_an_item_says_the_name_the_file_name_and_what_there_is(tmp_path):
    shipped, mine = tmp_path / "shipped", tmp_path / "mine"
    shipped.mkdir()
    mine.mkdir()
    (shipped / "crowd_cheer.wav").write_bytes(b"x")
    folders = (str(mine), str(shipped))
    assert SM.item_name("crowd_cheer", folders) == "The crowd cheers. File name crowd_cheer. the original sound"
    (mine / "crowd_cheer.wav").write_bytes(b"y")
    assert SM.item_name("crowd_cheer", folders) == "The crowd cheers. File name crowd_cheer. your sound"
    (mine / "crowd_cheer2.wav").write_bytes(b"y")
    assert SM.item_name("crowd_cheer", folders) == "The crowd cheers. File name crowd_cheer. 2 sounds, 2 of them yours"
    assert SM.item_name("mic_on", folders).startswith("The referee's microphone clicks on. File name mic_on.")


class FakeAudio:
    def __init__(self):
        self.library = types.SimpleNamespace(player_dir="", pick_file=lambda path: types.SimpleNamespace(sound=object()))
        self.played, self.stopped = [], 0

    def stop_preview(self):
        self.stopped += 1

    def play_file(self, slot, path, volume=0, pan=0):
        self.played.append((slot, os.path.basename(path), volume))
        return 0.0


def test_enter_plays_the_sound_at_its_level_in_the_game_and_again_plays_the_next_of_its_family(tmp_path):
    from gamerig import Rig
    rig = Rig(sounds_dir=tmp_path / "s", rng=__import__("random").Random(1))
    audio = FakeAudio()
    audio.library.player_dir = str(tmp_path / "mine")
    (tmp_path / "mine").mkdir()
    (tmp_path / "mine" / "crowd_roar2.wav").write_bytes(b"y")
    for key in (ENTER, ENTER, ENTER, DOWN, ESC):
        rig.keys.post(key)
    SM.sounds_list(rig.speech, rig.keys, audio, -300, lambda: 0.0)
    assert audio.played[:3] == [(7, "crowd_cheer.wav", ST.LEVELS["crowd_cheer"] - 300)] * 3         # the first sound has one file: the same again
    said = [t for t, *_ in rig.said]
    assert said[0].startswith("Stadium and referee sounds. 19 items. Press F1 for help. The crowd cheers. File name crowd_cheer.")
    assert "Sound 1 of 1, original." in said and audio.stopped >= 4


def test_the_whistles_play_at_the_level_of_the_game_s_whistle(tmp_path):
    from gamerig import Rig
    rig = Rig(sounds_dir=tmp_path / "s", rng=__import__("random").Random(1))
    audio = FakeAudio()
    audio.library.player_dir = str(tmp_path / "mine")
    for key in [END, ENTER, ESC]:
        rig.keys.post(key)
    SM.sounds_list(rig.speech, rig.keys, audio, 0, lambda: 0.0)
    assert audio.played == [(7, "whistle_triple.wav", ST.WHISTLE_LEVEL)]


def test_f1_in_the_list_says_how_to_use_your_own_file(tmp_path):
    text = X.TEXTS["NXM-52"] + X.TEXTS["NXM-53"]
    assert "put a file with the same name in your sounds folder" in text and "give it a number, like crowd_cheer2" in text
    assert "Delete your file to get the original back" in text and "only with the N. F. L. rules" in text


# ----- the Sounds menu -----

def test_the_sounds_menu_ends_with_the_list_and_the_put_back_item_and_the_check_reads_the_players_files(tmp_path, caplog):
    rig = rig_for(tmp_path, [])
    spoken = sounds_menu(rig, [DOWN] * 10)
    assert spoken[2].startswith("Sounds. 11 items.")
    assert spoken[11:13] == [X.text("NXM-47") + ".", X.text("NXM-54") + "."]
    caplog.set_level("INFO", logger="nfl4.game")
    (tmp_path / "sounds" / "crowd_boo.wav").write_bytes(b"RIFF not a sound")
    rig = rig_for(tmp_path, [])
    assert sounds_menu(rig, [DOWN, DOWN, DOWN, ENTER])[6] == words.checked(1)


def test_put_back_asks_once_moves_the_files_and_says_how_many(tmp_path):
    rig = rig_for(tmp_path, [])
    (tmp_path / "sounds" / "crowd_cheer.wav").write_bytes(b"y")
    (tmp_path / "sounds" / "whistle_short.wav").write_bytes(b"y")
    spoken = sounds_menu(rig, [DOWN] * 10 + [ENTER, ESC])                       # any key but Enter cancels
    assert spoken[-3] == X.text("NXM-55") and spoken[-2] == words.NOTHING_CHANGED
    assert (tmp_path / "sounds" / "crowd_cheer.wav").exists()
    rig = rig_for(tmp_path, [])
    spoken = sounds_menu(rig, [DOWN] * 10 + [ENTER, ENTER])
    assert X.text("NXM-56", n=2) in spoken and not (tmp_path / "sounds" / "crowd_cheer.wav").exists()
    assert len(os.listdir(tmp_path / "sounds" / "removed sounds")) == 2
    rig = rig_for(tmp_path, [])
    assert X.text("NXM-57") in sounds_menu(rig, [DOWN] * 10 + [ENTER, ENTER])
