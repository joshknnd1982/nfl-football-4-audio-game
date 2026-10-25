"""favourites.txt, the player's favourite plays (nfl4 only, rule 0.13; design `spec/NFL_PLAYS_DESIGN.md` 2.5; SX.10b). This is
inspired by Jim Kitchen."""
import os

from nfl4.data import customlists as cl
from nfl4.extras.plays import favourites as F
from nfl4.extras.plays import play_menus as P


def path_of(folder):
    return os.path.join(str(folder), "playbooks", "favourites.txt")


def test_a_missing_file_is_made_empty_and_read_as_no_favourites(tmp_path):
    offense, defense, load, problems = F.read(str(tmp_path))
    assert (offense, defense) == ((), ()) and load.status == cl.CREATED and problems.count == 0
    assert open(path_of(tmp_path), encoding="utf-8").read().startswith("# NFL Football 4 favourite plays, format 1.")


def test_what_is_written_is_read_back_in_its_order(tmp_path):
    favs = ()
    for pid in ("O027", "O031", "O046"):
        favs, _said = P.add_favourite(favs, pid)
    assert F.write(str(tmp_path), favs, ("D017", "D011"))
    offense, defense, load, problems = F.read(str(tmp_path))
    assert offense == ("O027", "O031", "O046") and defense == ("D017", "D011") and load.status == cl.OK
    assert problems.count == 0


def test_bad_lines_are_problems_and_left_out_never_the_whole_file(tmp_path):
    os.makedirs(os.path.dirname(path_of(tmp_path)))
    with open(path_of(tmp_path), "w", encoding="utf-8") as handle:
        handle.write("# NFL Football 4 favourite plays, format 1.\n"
                     "OF01 = O027\nOF02 = D017\nOF03 = O999\nOF11 = O001\nOF01 = O002\nOF04 = O027\n"
                     "DF02 = D011\nXX01 = O001\nnot a line\nDF01 = d017\n")
    offense, defense, load, problems = F.read(str(tmp_path))
    assert offense == ("O027",) and defense == ("D017", "D011")
    assert problems.count == 7 and load.status == cl.OK


def test_a_damaged_file_is_copied_aside_and_made_again(tmp_path):
    os.makedirs(os.path.dirname(path_of(tmp_path)))
    with open(path_of(tmp_path), "wb") as handle:
        handle.write(b"\x00\xff\xfe garbage")
    offense, defense, load, _problems = F.read(str(tmp_path))
    assert (offense, defense) == ((), ()) and load.status == cl.RESET
    assert any(name.startswith("favourites.txt.damaged") for name in os.listdir(os.path.dirname(path_of(tmp_path))))


def test_only_ten_a_side_are_written():
    text = F.text_of(tuple("O%03d" % n for n in range(1, 15)), ())
    assert "OF10 = O010" in text and "OF11" not in text
