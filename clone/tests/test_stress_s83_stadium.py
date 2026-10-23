"""The stadium and referee sounds the player adds, under stress (S8.3 round 2; nfl4 only, rule 0.13; SZ.2, D-107; rule 0.14). This is inspired by
Jim Kitchen.

FOUND HERE: a family the player filled with thousands of files was read whole at every crowd sound (the folder listed again and every file of
the family decoded to see whether it could be used): 2,000 files of crowd_cheer stalled the game thread for 14.6 seconds at the first cheer and
0.8 seconds at every later one (work\\s83b\\probe_stadium_many.py). Now the scan reads only the names of the family (no cache: Windows did not move a folder's time
in time, so a cache missed a file just added), one file is drawn
and only that one is read; a damaged one is left out and the draw made again, at most MAX_TRIES times, then the shipped sound plays.
"""
import os
import random
import time
import types

import pytest
import filedamage
from test_sz2_custom_sounds import FakeLibrary, stadium_with
from wavmaker import sine, write

from nfl4.audio.library import SoundLibrary, shipped_sounds_dir
from nfl4.extras import stadium as ST
from nfl4.game.rnd import GameRandom


def folders(tmp_path):
    (tmp_path / "mine").mkdir()
    (tmp_path / "shipped").mkdir()
    (tmp_path / "shipped" / "crowd_cheer.wav").write_bytes(b"shipped")
    return tmp_path / "mine"


def seeded(st, seed=1):
    st.rnd = GameRandom(random.Random(seed))
    return st


def test_thousands_of_the_players_files_cost_one_read_per_sound(tmp_path):
    mine = folders(tmp_path)
    for n in range(1, 3001):
        (mine / ("crowd_cheer%d.wav" % n)).write_bytes(b"y")
    for n in range(1, 2001):
        (mine / ("unrelated%d.ogg" % n)).write_bytes(b"z")
    library = FakeLibrary()
    st = seeded(stadium_with(tmp_path, library))
    st.pick("crowd_cheer")
    began = time.perf_counter()
    for _ in range(500):
        st.pick("crowd_cheer")
    each = (time.perf_counter() - began) / 500
    assert each < 0.05, each                                                        # was 0.8 s (the real library) before the fix
    assert len(library.asked) == 501                                                # one file read per sound, never the whole family


def test_with_the_real_library_two_hundred_long_files_do_not_stall_the_first_cheer(tmp_path):
    mine = folders(tmp_path)
    one = mine / "crowd_cheer.wav"
    write(one, sine(440, 1.0, 22050), rate=22050)
    raw = one.read_bytes()
    for n in range(2, 201):
        (mine / ("crowd_cheer%d.wav" % n)).write_bytes(raw)
    st = seeded(stadium_with(tmp_path, SoundLibrary(shipped_sounds_dir(), str(mine))))
    began = time.perf_counter()
    path = st.pick("crowd_cheer")
    assert time.perf_counter() - began < 0.5 and os.path.dirname(path) == str(mine)


def test_a_damaged_file_is_left_out_and_the_draw_made_again_among_the_others(tmp_path):
    mine = folders(tmp_path)
    for n in (1, 2, 3):
        (mine / ("crowd_cheer%d.wav" % n)).write_bytes(b"y")
    st = seeded(stadium_with(tmp_path, FakeLibrary(bad=("crowd_cheer2.wav",))))
    picked = {os.path.basename(st.pick("crowd_cheer")) for _ in range(200)}
    assert picked == {"crowd_cheer1.wav", "crowd_cheer3.wav"}


def test_a_family_of_only_damaged_files_plays_the_shipped_sound_after_a_few_tries(tmp_path, monkeypatch):
    mine = folders(tmp_path)
    for n in range(1, 101):
        (mine / ("crowd_cheer%d.wav" % n)).write_bytes(b"bad")
    library = FakeLibrary(bad=(os.sep + "mine" + os.sep,))
    st = seeded(stadium_with(tmp_path, library))
    from nfl4.data import debuglog
    seen = []
    real = debuglog.event
    monkeypatch.setattr(debuglog, "event", lambda *a, **f: (seen.append(a[1]), real(*a, **f))[1])
    path = st.pick("crowd_cheer")
    assert os.path.basename(os.path.dirname(path)) == "shipped"
    assert len([p for p in library.asked if os.sep + "mine" + os.sep in p]) == ST.MAX_TRIES
    assert "stadium_files_skipped" in seen                                          # rule 0.15: the log says why the shipped sound played


def test_a_file_added_or_removed_while_the_program_runs_is_seen_at_the_next_sound(tmp_path):
    mine = folders(tmp_path)
    (mine / "crowd_cheer.wav").write_bytes(b"y")
    st = seeded(stadium_with(tmp_path, FakeLibrary()))
    assert {os.path.basename(st.pick("crowd_cheer")) for _ in range(20)} == {"crowd_cheer.wav"}
    (mine / "crowd_cheer2.wav").write_bytes(b"y")
    assert {os.path.basename(st.pick("crowd_cheer")) for _ in range(200)} == {"crowd_cheer.wav", "crowd_cheer2.wav"}
    (mine / "crowd_cheer.wav").unlink()                                             # the shipped crowd_cheer.wav takes its number again
    where = {(os.path.basename(os.path.dirname(p)), os.path.basename(p)) for p in (st.pick("crowd_cheer") for _ in range(200))}
    assert where == {("shipped", "crowd_cheer.wav"), ("mine", "crowd_cheer2.wav")}


@pytest.mark.parametrize("state", ["folder_in_place", "held_open", "empty", "huge", "binary_zeros", "folder_gone"])
def test_the_real_library_with_a_file_in_a_bad_state_never_raises_and_plays_something(tmp_path, state):
    mine = folders(tmp_path)
    write(tmp_path / "shipped" / "crowd_cheer.wav", sine(440, 0.2, 22050), rate=22050)
    target = mine / "crowd_cheer.wav"
    write(target, sine(440, 0.2, 22050), rate=22050)
    context = None
    if state == "folder_in_place":
        target.unlink()
        target.mkdir()
    elif state == "held_open":
        context = filedamage.holding(target)
    elif state == "folder_gone":
        import shutil
        shutil.rmtree(mine)
    else:
        filedamage.apply(state, target)
    library = SoundLibrary(shipped_sounds_dir(), str(mine))
    st = seeded(stadium_with(tmp_path, library))
    if context is None:
        path = st.pick("crowd_cheer")
    else:
        with context:
            path = st.pick("crowd_cheer")
    assert path is not None and library.pick_file(path).sound is not None or os.path.basename(os.path.dirname(path)) == "shipped"


def test_with_every_file_usable_the_draws_are_the_ones_the_whole_list_gave(tmp_path):
    mine = folders(tmp_path)
    for n in range(1, 8):
        (mine / ("crowd_cheer%d.wav" % n)).write_bytes(b"y")
    a, b = seeded(stadium_with(tmp_path, FakeLibrary()), 5), seeded(stadium_with(tmp_path, FakeLibrary()), 5)
    old = []
    for _ in range(100):
        files = b.files("crowd_cheer")
        old.append(files[b.rnd(len(files)) - 1])
    assert [a.pick("crowd_cheer") for _ in range(100)] == old
