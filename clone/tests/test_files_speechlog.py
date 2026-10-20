"""footballlog.txt: the speech log (data/files/speechlog.py). This is inspired by Jim Kitchen.

GAME_SPEC 12, GAP_REGISTER G-S10: Output (a new file) at a fresh season's first week, else Append; one line per Print #3; a
file over 1 MB is started again; a write error switches the log off and never reaches the player.
"""
import os

from nfl4.data.files.speechlog import SpeechLog


def read(path):
    with open(path, "rb") as handle:
        return handle.read()


def test_a_fresh_log_starts_a_new_file_and_an_ordinary_one_appends(tmp_path):
    path = str(tmp_path / "footballlog.txt")
    log = SpeechLog(path)
    log.open(fresh=True)
    log.line("NFL Football 4 by Josh Kennedy, inspired by Jim Kitchen")
    log.line("")
    log.close()
    assert read(path) == b"NFL Football 4 by Josh Kennedy, inspired by Jim Kitchen\r\n\r\n"
    log.open(fresh=False)
    log.line(" This is week #2 of Josh Kennedy's N. F. L. football ")
    log.close()
    assert read(path).endswith(b"\r\n\r\n This is week #2 of Josh Kennedy's N. F. L. football \r\n")
    log.open(fresh=True)
    log.close()
    assert read(path) == b""                                    # Output: the old file is gone


def test_a_line_before_the_log_is_open_is_dropped_and_after_closing_too(tmp_path):
    log = SpeechLog(str(tmp_path / "footballlog.txt"))
    log.line("nobody listens")
    log.open(True)
    log.line("one")
    log.close()
    log.line("two")
    assert read(str(tmp_path / "footballlog.txt")) == b"one\r\n"


def test_lines_are_on_disk_at_once_not_when_the_program_ends(tmp_path):
    path = str(tmp_path / "footballlog.txt")
    log = SpeechLog(path)
    log.open(True)
    log.line("TOUCH DOWN")
    assert read(path) == b"TOUCH DOWN\r\n"                       # the process may end through os._exit
    log.close()


def test_letters_above_127_are_utf_8(tmp_path):
    path = str(tmp_path / "footballlog.txt")
    log = SpeechLog(path)
    log.open(True)
    log.line("Martínez")
    log.close()
    assert read(path).decode("utf-8") == "Martínez\r\n"


def test_a_file_over_the_cap_is_started_again_when_opened_for_appending(tmp_path):
    path = tmp_path / "footballlog.txt"
    path.write_bytes(b"x" * 600)
    log = SpeechLog(str(path), cap=500)
    log.open(fresh=False)
    log.line("new")
    log.close()
    assert path.read_bytes() == b"new\r\n"
    path.write_bytes(b"y" * 400)
    log.open(fresh=False)
    log.line("more")
    log.close()
    assert path.read_bytes() == b"y" * 400 + b"more\r\n"


def test_a_log_that_grows_past_the_cap_in_a_run_starts_again(tmp_path):
    path = tmp_path / "footballlog.txt"
    log = SpeechLog(str(path), cap=100)
    log.open(True)
    for number in range(40):
        log.line("line %02d" % number)
    log.close()
    text = path.read_bytes().decode()
    assert len(text) <= 100 + 20 and text.endswith("line 39\r\n") and "line 00" not in text


def test_an_unwritable_place_switches_the_log_off_without_an_error(tmp_path):
    blocker = tmp_path / "not a folder"
    blocker.write_text("a file where the folder should be")
    log = SpeechLog(str(blocker / "footballlog.txt"))
    log.open(True)
    assert not log.is_open
    log.line("nothing happens")
    log.close()


def test_a_line_the_file_cannot_encode_does_not_stop_the_log(tmp_path):
    path = tmp_path / "footballlog.txt"
    log = SpeechLog(str(path))
    log.open(True)
    log.line("good")
    log.line("bad \ud800 surrogate")                            # cannot be written as UTF-8
    assert not log.is_open                                       # the log gave up; the game is not told
    log.line("after")
    log.close()
    assert path.read_bytes().startswith(b"good\r\n")


def test_a_log_held_open_by_another_handle_of_ours_is_replaced_by_open(tmp_path):
    path = str(tmp_path / "footballlog.txt")
    log = SpeechLog(path)
    log.open(True)
    log.line("first run")
    log.open(True)                                               # a second open closes the first handle
    log.line("second run")
    log.close()
    assert read(path) == b"second run\r\n" and os.path.getsize(path) == 12
