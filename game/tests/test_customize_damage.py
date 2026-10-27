"""The 7.10 damage matrix for every customization file, and a fuzz of random corruptions (S7.7). This is inspired by Jim Kitchen.

Playbook 7.10: for each resource file in turn delete it, delete its folder, empty it, cut it in half, fill it with random bytes,
save it in another encoding, make it huge, make it read-only, hold it open in another program, give it a newer format version,
put a bad line in the middle. After each the game starts, speaks, and plays with the original values (or the player's good
entries), the file is made again or a copy of the damaged one is saved, nothing raises. What was written down before the code:
the player's footplay.txt and the player's sound files are never touched by any of it; the loaded values are always valid
(32 different team names, 8 different division names, 1,708 surnames that pass the limits); a file that is unusable gives ONE
sentence naming it, a bad line gives the count of problems. BC.2 (D-180): banter.txt is gone, so the matrix covers the three lists.
"""
import os
import random
import shutil

import pytest

from filedamage import BYTE_DAMAGES, apply, holding, read_only
from nfl4.data import customlists as cl
from nfl4.data.customize import SPECS, Customization, name_problem
from nfl4.game import league as league_module
from nfl4.game.names import POOL_SIZE, load_surnames
from wavmaker import sine, write

DEFAULTS = {"teams": league_module.DEFAULT_TEAM_NAMES, "divisions": league_module.DEFAULT_DIVISION_NAMES}
UNUSABLE = ("empty", "random_bytes", "other_encoding", "huge", "newer_format", "no_header", "binary_zeros",
            "another_list_header")
FOOTPLAY = b"Running Backs:\r\nA\r\nB\r\nC\r\nD\r\nE\r\nF\r\nReceivers:\r\n"


def start(tmp_path, tag="x"):
    folder = tmp_path / tag / "customize"
    custom = Customization(str(folder))
    (folder / "footplay.txt").write_bytes(FOOTPLAY)
    write(folder / "sounds" / "mine.wav", sine(440, 0.1, 11025), rate=11025)
    return custom, folder


def assert_valid(snapshot):
    assert len({n.casefold() for n in snapshot.team_names}) == 32
    assert len({n.casefold() for n in snapshot.division_names}) == 8
    assert all(name_problem(n) is None for n in snapshot.team_names + snapshot.division_names)
    if snapshot.surnames is not None:
        assert len(snapshot.surnames) == POOL_SIZE and all(name_problem(n) is None for n in snapshot.surnames)


def assert_player_files_kept(folder):
    assert (folder / "footplay.txt").read_bytes() == FOOTPLAY
    assert (folder / "sounds" / "mine.wav").exists()


def default_snapshot_values(snapshot, key):
    if key == "teams":
        return snapshot.team_names == league_module.DEFAULT_TEAM_NAMES
    if key == "divisions":
        return snapshot.division_names == league_module.DEFAULT_DIVISION_NAMES
    if key == "surnames":
        return snapshot.surnames == load_surnames()
    raise KeyError(key)


KEYS = [spec.key for spec in SPECS]


@pytest.mark.parametrize("key", KEYS)
@pytest.mark.parametrize("kind", UNUSABLE)
def test_an_unusable_file_is_copied_aside_made_again_told_once_and_the_originals_are_used(tmp_path, key, kind):
    custom, folder = start(tmp_path)
    spec = next(s for s in SPECS if s.key == key)
    path = folder / spec.file_name
    apply(kind, path)
    damaged = path.read_bytes()
    custom = Customization(str(folder))
    snap = custom.snapshot
    assert snap.statuses[key] == cl.RESET and snap.problem_count(key) == 0
    assert [n for n in snap.notices if spec.file_name in n] == [
        " The file %s was damaged and has been reset to %s. A copy was saved. " % (spec.file_name, spec.original_nouns)]
    assert (folder / (spec.file_name + ".damaged1")).read_bytes() == damaged
    assert_valid(snap)
    assert default_snapshot_values(snap, key)
    assert_player_files_kept(folder)
    again = Customization(str(folder))                                  # the file is whole again: nothing more is said
    assert again.snapshot.notices == [] and again.snapshot.statuses[key] == cl.OK


@pytest.mark.parametrize("key", KEYS)
def test_a_cut_file_uses_what_is_left_and_the_originals_for_the_rest(tmp_path, key):
    custom, folder = start(tmp_path)
    path = folder / next(s for s in SPECS if s.key == key).file_name
    apply("cut_in_half", path)
    snap = Customization(str(folder)).snapshot
    assert snap.statuses[key] == cl.OK and not (folder / (path.name + ".damaged1")).exists()
    assert_valid(snap)
    if key == "surnames":                                               # every name cut off in the middle is still a name
        assert snap.surnames[POOL_SIZE - 1] == load_surnames()[POOL_SIZE - 1]
    assert_player_files_kept(folder)


@pytest.mark.parametrize("key", KEYS)
def test_a_bad_line_in_the_middle_is_counted_the_good_entries_stay_and_the_file_is_not_replaced(tmp_path, key):
    custom, folder = start(tmp_path)
    spec = next(s for s in SPECS if s.key == key)
    path = folder / spec.file_name
    first_id = {"teams": "T09 = Broncos", "divisions": "D3 = A. F. C. West.", "surnames": "S0001 = "}[key]
    text = path.read_bytes().decode("utf-8")
    text = text.replace(first_id, first_id.replace("Broncos", "Mustangs").replace("West.", "West Side.")
                        .replace("S0001 = ", "S0001 = Zed "), 1)
    path.write_bytes(text.encode("utf-8"))
    apply("bad_line_in_the_middle", path)
    changed = path.read_bytes()
    snap = Customization(str(folder)).snapshot
    assert snap.statuses[key] == cl.OK and snap.problem_count(key) == 2
    assert snap.notices == [" 2 problems found in %s, details are in the log. " % spec.file_name]
    assert path.read_bytes() == changed and not (folder / (path.name + ".damaged1")).exists()
    assert_valid(snap)
    if key == "teams":
        assert snap.team_names[8] == "Mustangs"
    elif key == "divisions":
        assert snap.division_names[2] == "A. F. C. West Side."
    else:
        assert snap.surnames[0].startswith("Zed ")
    assert_player_files_kept(folder)


@pytest.mark.parametrize("key", KEYS)
def test_a_deleted_file_and_a_deleted_folder_are_made_again_silently(tmp_path, key):
    custom, folder = start(tmp_path)
    spec = next(s for s in SPECS if s.key == key)
    (folder / spec.file_name).unlink()
    snap = Customization(str(folder)).snapshot
    assert snap.statuses[key] == cl.CREATED and snap.notices == [] and default_snapshot_values(snap, key)
    assert (folder / spec.file_name).exists()
    shutil.rmtree(folder)
    snap = Customization(str(folder)).snapshot
    assert snap.notices == [] and all((folder / s.file_name).exists() for s in SPECS)
    assert (folder / "sounds").is_dir()
    assert_valid(snap)


@pytest.mark.parametrize("key", KEYS)
def test_a_read_only_file_that_is_fine_is_read_and_one_that_is_damaged_is_not_replaced(tmp_path, key):
    custom, folder = start(tmp_path)
    spec = next(s for s in SPECS if s.key == key)
    path = folder / spec.file_name
    with read_only(path):
        snap = Customization(str(folder)).snapshot
        assert snap.statuses[key] == cl.OK and snap.notices == []
    path.write_bytes(b"junk")
    with read_only(path):
        snap = Customization(str(folder)).snapshot
        assert snap.statuses[key] == cl.KEPT_DAMAGED and default_snapshot_values(snap, key)
        assert snap.notices == [" The file %s is damaged and could not be replaced. %s are used this time. "
                                % (spec.file_name, spec.original_nouns.capitalize())]
        assert path.read_bytes() == b"junk" and (folder / (spec.file_name + ".damaged1")).exists()
        assert_valid(snap)
    assert_player_files_kept(folder)


@pytest.mark.parametrize("key", KEYS)
def test_a_file_another_program_holds_is_not_damage_and_nothing_is_written_over_it(tmp_path, key):
    custom, folder = start(tmp_path)
    spec = next(s for s in SPECS if s.key == key)
    path = folder / spec.file_name
    before = path.read_bytes()
    with holding(path):
        snap = Customization(str(folder)).snapshot
        assert snap.statuses[key] == cl.LOCKED and default_snapshot_values(snap, key)
        assert snap.notices == [" The file %s is in use by another program. %s are used this time. "
                                % (spec.file_name, spec.original_nouns.capitalize())]
        assert not [n for n in os.listdir(folder) if ".damaged" in n or n.endswith(".tmp")]
        assert_valid(snap)
    assert path.read_bytes() == before and Customization(str(folder)).snapshot.notices == []


def test_a_file_over_eight_megabytes_is_moved_aside_not_copied_and_made_again(tmp_path):
    custom, folder = start(tmp_path)
    path = folder / "teams.txt"
    path.write_bytes(b"# NFL Football 4 teams, format 1.\r\n" + b"# x\r\n" * 2_000_000)
    size = path.stat().st_size
    assert size > 8_000_000
    snap = Customization(str(folder)).snapshot
    assert snap.statuses["teams"] == cl.RESET and (folder / "teams.txt.damaged1").stat().st_size == size
    assert (folder / "teams.txt").stat().st_size < 10_000
    assert_valid(snap)


def test_three_damaged_copies_are_kept_per_file_and_the_oldest_goes(tmp_path):
    custom, folder = start(tmp_path)
    for number in range(5):
        (folder / "divisions.txt").write_bytes(b"junk %d" % number)
        Customization(str(folder))
    names = sorted(n for n in os.listdir(folder) if n.startswith("divisions.txt.damaged"))
    assert names == ["divisions.txt.damaged3", "divisions.txt.damaged4", "divisions.txt.damaged5"]


def test_a_reload_after_the_file_was_damaged_in_play_heals_it_and_says_so_while_the_loaded_values_stay_until_then(tmp_path):
    custom, folder = start(tmp_path)
    text = (folder / "teams.txt").read_bytes().decode("utf-8").replace("T09 = Broncos", "T09 = Mustangs")
    (folder / "teams.txt").write_bytes(text.encode("utf-8"))
    custom.reload()
    assert custom.snapshot.team_names[8] == "Mustangs"
    (folder / "teams.txt").write_bytes(b"\x00\x00junk")
    assert custom.take_notices() == [] and custom.snapshot.team_names[8] == "Mustangs"       # in play: nothing changes
    notices = custom.reload()
    assert notices == [" The file teams.txt was damaged and has been reset to the original team names. A copy was saved. "]
    assert custom.snapshot.team_names[8] == "Broncos" and (folder / "teams.txt.damaged1").read_bytes() == b"\x00\x00junk"


# ----- the fuzz -----

def corrupt(rng, raw: bytes) -> bytes:
    kind = rng.randrange(9)
    if kind == 0:
        return b""
    if kind == 1:
        return raw[:rng.randrange(len(raw) + 1)]
    if kind == 2:
        data = bytearray(raw)
        for _ in range(rng.randint(1, 40)):
            if data:
                data[rng.randrange(len(data))] = rng.randrange(256)
        return bytes(data)
    if kind == 3:
        at = rng.randrange(len(raw) + 1)
        return raw[:at] + bytes(rng.randrange(256) for _ in range(rng.randint(1, 200))) + raw[at:]
    if kind == 4:
        lines = raw.split(b"\n")
        for _ in range(rng.randint(1, 30)):
            if lines:
                del lines[rng.randrange(len(lines))]
        return b"\n".join(lines)
    if kind == 5:
        lines = raw.split(b"\n")
        for _ in range(rng.randint(1, 30)):
            index = rng.randrange(len(lines))
            lines.insert(rng.randrange(len(lines) + 1), lines[index])
        return b"\n".join(lines)
    if kind == 6:
        return bytes(rng.randrange(256) for _ in range(rng.randint(0, 3000)))
    if kind == 7:
        return raw.decode("utf-8", errors="replace").encode(rng.choice(["utf-16", "utf-16-le", "cp1252", "utf-8-sig"]), errors="replace")
    return raw.replace(rng.choice([b"=", b"[", b"]", b"|", b"T", b"B"]), rng.choice([b"", b"==", b"[[", b"\x00", b"\xff"]))


def test_a_few_hundred_random_corruptions_never_raise_and_never_touch_the_players_own_files(tmp_path):
    rng = random.Random(20261015)
    base = tmp_path / "base"
    Customization(str(base / "customize"))
    originals = {spec.file_name: (base / "customize" / spec.file_name).read_bytes() for spec in SPECS}
    for round_ in range(300):
        folder = tmp_path / ("f%d" % round_) / "customize"
        os.makedirs(folder / "sounds", exist_ok=True)
        for name, raw in originals.items():
            (folder / name).write_bytes(raw)
        (folder / "footplay.txt").write_bytes(FOOTPLAY)
        write(folder / "sounds" / "mine.wav", sine(440, 0.1, 11025), rate=11025)
        for spec in rng.sample(SPECS, rng.randint(1, 3)):
            path = folder / spec.file_name
            path.write_bytes(corrupt(rng, path.read_bytes()))
        custom = Customization(str(folder))
        assert_valid(custom.snapshot)
        for notice in custom.snapshot.notices:
            assert notice.startswith(" ") and notice.endswith(" ") and len(notice) < 200
        custom.reload()
        assert_valid(custom.snapshot)
        assert isinstance(custom.check(), str)
        custom.reset(rng.choice([None] + [s.key for s in SPECS]))
        custom.reload()
        assert_valid(custom.snapshot)
        assert not [n for n in os.listdir(folder) if n.endswith(".tmp")]
        for spec in SPECS:
            copies = [n for n in os.listdir(folder) if n.startswith(spec.file_name + ".damaged")]
            assert len(copies) <= 3, copies
        assert_player_files_kept(folder)
