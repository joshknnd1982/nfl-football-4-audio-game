"""The process never holds the program folder and always really ends (owner bug 2026-10-13: the program folder could not
be deleted after uninstalling, "folder in use"). This is inspired by Jim Kitchen's Brain.
"""
import logging
import os
import threading
import time

import nfl4.data.lifecycle as lifecycle
from nfl4.data.lifecycle import arm_exit_deadline, finish, leave_program_folder


def test_a_process_inside_the_program_folder_is_moved_out_of_it(tmp_path, monkeypatch):
    program = tmp_path / "Program Files" / "My Brain"
    program.mkdir(parents=True)
    safe = tmp_path / "data"
    monkeypatch.chdir(program)
    moved = leave_program_folder(str(program), str(safe))
    assert moved == str(safe) and os.path.samefile(os.getcwd(), safe)
    program.rename(tmp_path / "renamed")                              # nothing holds the folder any more


def test_a_process_in_a_folder_below_the_program_folder_is_moved_too(tmp_path, monkeypatch):
    program = tmp_path / "app"
    (program / "assets" / "sounds").mkdir(parents=True)
    monkeypatch.chdir(program / "assets" / "sounds")
    assert leave_program_folder(str(program), str(tmp_path / "data")) is not None
    assert not os.path.normcase(os.getcwd()).startswith(os.path.normcase(str(program)))


def test_a_process_elsewhere_is_left_alone(tmp_path, monkeypatch):
    program, elsewhere = tmp_path / "app", tmp_path / "somewhere"
    program.mkdir()
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)
    assert leave_program_folder(str(program), str(tmp_path / "data")) is None
    assert os.path.samefile(os.getcwd(), elsewhere)
    (tmp_path / "appendix").mkdir()
    monkeypatch.chdir(tmp_path / "appendix")                          # a folder whose name only starts the same way
    assert leave_program_folder(str(program), str(tmp_path / "data")) is None


def test_when_the_safe_folder_cannot_be_made_the_temp_folder_is_used(tmp_path, monkeypatch):
    program = tmp_path / "app"
    program.mkdir()
    blocker = tmp_path / "file"
    blocker.write_text("not a folder")
    monkeypatch.chdir(program)
    moved = leave_program_folder(str(program), str(blocker / "inside"))
    assert moved is not None and os.path.samefile(os.getcwd(), moved)
    assert not os.path.normcase(os.getcwd()).startswith(os.path.normcase(str(program)))


def test_the_exit_deadline_ends_the_process_after_its_time_and_can_be_cancelled(caplog):
    ended = []
    caplog.set_level(logging.WARNING)
    arm_exit_deadline(0.05, exit_fn=ended.append, code=0)
    time.sleep(0.4)
    assert ended == [0] and "ending the process" in caplog.text
    ended.clear()
    timer = arm_exit_deadline(0.2, exit_fn=ended.append)
    timer.cancel()
    time.sleep(0.5)
    assert ended == []


def test_finish_flushes_the_log_and_ends_the_process_with_the_code(tmp_path):
    handler = logging.FileHandler(tmp_path / "x.log", encoding="utf-8")
    log = logging.getLogger("lifecycle_test")
    log.addHandler(handler)
    log.setLevel(logging.INFO)
    log.info("the last line")
    codes = []
    finish(0, exit_fn=codes.append)
    assert codes == [0]
    assert "the last line" in (tmp_path / "x.log").read_text(encoding="utf-8")
    finish(None, exit_fn=codes.append)                                # not a number: a clean exit, never a crash
    assert codes == [0, 0]
    log.removeHandler(handler)


def test_the_deadline_timer_is_a_daemon_so_it_never_keeps_the_process_alive():
    timer = arm_exit_deadline(30.0, exit_fn=lambda code: None)
    try:
        assert timer.daemon and isinstance(timer, threading.Timer)
    finally:
        timer.cancel()
    assert lifecycle.EXIT_DEADLINE_SECONDS >= 3
