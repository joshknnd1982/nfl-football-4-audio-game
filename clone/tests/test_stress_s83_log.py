"""The log and the problem report under stress (S8.3; playbook 7.11, rule 0.15). This is inspired by Jim Kitchen.

tests/test_debuglog.py holds the contract one condition at a time. Here the conditions meet the size of a real bad day: a launch log at its
cap read into a report with the account name all through it, a destination that fills up halfway through the zip, folders that are files,
logs that are directories, binary junk, a log written by the running program while the report reads it, the program started with its logs
folder blocked, full or locked, and a long play session that must keep the caps and the redaction.
"""
import errno
import getpass
import logging
import os
import re
import threading
import time
import zipfile

import pytest

import nfl4.app as app
import nfl4.ui.window as window_module
from nfl4.data import debuglog, problem_report
from nfl4.game import texts
from test_app_startup import Made, closing_after
from test_debuglog import begin, leaks, written

USER = getpass.getuser()
SYSTEM = dict(system_kwargs=dict(args=[], settings=None))


def big_log(path, megabytes, user=USER):
    """A log of about `megabytes` MB whose every line holds a path with the account name, the way a bad day's log looks."""
    line = ("12:00:00.000 +0.001 DEBUG game file abc123 read path=C:\\Users\\%s\\AppData\\Roaming\\NFL Football 4\\footbal1.dat "
            "chars=%d result=ok ms=0.4 mail=%s@example.com\n")
    with open(path, "w", encoding="utf-8") as handle:
        written_bytes, n = 0, 0
        while written_bytes < megabytes * 1024 * 1024:
            text = line % (user, n, user)
            handle.write(text)
            written_bytes += len(text)
            n += 1


@pytest.fixture
def data(tmp_path, monkeypatch):
    folder = tmp_path / "data"
    folder.mkdir()
    monkeypatch.setenv("NFL4_DATA_DIR", str(folder))
    monkeypatch.setattr(problem_report, "log_folders", lambda: [str(folder / "logs")])
    (folder / "logs").mkdir()
    return folder


def test_three_launches_at_their_cap_make_a_report_in_time_with_the_account_name_nowhere(data, tmp_path):
    for n in range(3):
        big_log(data / "logs" / ("nfl4-202610%02d-100000.log" % (n + 1)), 5)
        big_log(data / "logs" / ("nfl4-202610%02d-100000-b.log" % (n + 1)), 5)
    started = time.monotonic()
    path = problem_report.make(False, str(tmp_path / "out"), **SYSTEM)
    seconds = time.monotonic() - started
    assert seconds < 60, seconds
    with zipfile.ZipFile(path) as bundle:
        logs = [n for n in bundle.namelist() if n.startswith("logs/")]
        assert len(logs) == 6
        for member in logs:
            text = bundle.read(member).decode("utf-8")
            assert not leaks(text, USER) and f"{USER}@" not in text, member
    assert os.path.getsize(path) < 40 * 1024 * 1024


def test_a_destination_that_fills_up_in_the_middle_raises_one_clean_error_and_leaves_no_half_zip(data, tmp_path, monkeypatch):
    import zipfile as zf
    for n in range(3):
        big_log(data / "logs" / ("nfl4-202610%02d-100000.log" % (n + 1)), 1)
    real = zf.ZipFile.writestr
    calls = {"n": 0}

    def full(self, *args, **kwargs):
        calls["n"] += 1
        if calls["n"] >= 4:
            raise OSError(errno.ENOSPC, "No space left on device")
        return real(self, *args, **kwargs)
    monkeypatch.setattr(zf.ZipFile, "writestr", full)
    out = tmp_path / "out"
    with pytest.raises(OSError):
        problem_report.make(False, str(out), **SYSTEM)
    assert [n for n in os.listdir(out)] == [], "a half-written zip was left where the player looks for the report"


def test_a_destination_that_is_a_file_raises_an_error_and_the_command_line_says_so_with_code_1(data, tmp_path, capsys):
    blocker = tmp_path / "blocker"
    blocker.write_text("a file where the folder should be")
    with pytest.raises(OSError):
        problem_report.make(False, str(blocker), **SYSTEM)
    assert app.main(["--problem-report", "--quiet", "--folder=" + str(blocker)]) == 1
    assert "could not be made" in capsys.readouterr().out


def test_logs_that_are_folders_binary_junk_or_not_text_are_skipped_or_read_and_the_report_is_still_made(data, tmp_path):
    logs = data / "logs"
    (logs / "nfl4-20261001-100000.log").mkdir()
    (logs / "nfl4-20261002-100000.log").write_bytes(bytes(range(256)) * 400)
    (logs / "nfl4-20261003-100000.log").write_bytes(("C:\\Users\\%s\\x \u00fcn\u00ef\n" % USER).encode("utf-16"))
    (logs / "nfl4-20261004-100000.log").write_bytes(b"")
    (logs / "nfl4-crash.log").mkdir()
    path = problem_report.make(False, str(tmp_path / "out"), **SYSTEM)
    names = problem_report.listing(path)
    assert "README.txt" in names and "system.txt" in names and "customization.txt" in names


def test_the_report_made_while_the_program_writes_its_log_holds_what_was_written_so_far(tmp_path, monkeypatch):
    monkeypatch.setenv("NFL4_DATA_DIR", str(tmp_path / "data"))
    logs = tmp_path / "data" / "logs"
    path = begin(logs)
    monkeypatch.setattr(problem_report, "log_folders", lambda: [str(logs)])
    stop = threading.Event()

    def writer():
        n = 0
        while not stop.is_set():
            debuglog.event("app", "busy_writing", n=n, path="C:\\Users\\%s\\x" % USER)
            n += 1
            time.sleep(0.0005)                        # a thousand lines a second is far more than the program writes
    thread = threading.Thread(target=writer, daemon=True)
    thread.start()
    try:
        report = problem_report.make(False, str(tmp_path / "out"), **SYSTEM)
    finally:
        stop.set()
        thread.join(5)
    with zipfile.ZipFile(report) as bundle:
        member = [n for n in bundle.namelist() if n.startswith("logs/")][0]
        text = bundle.read(member).decode("utf-8")
        assert "busy_writing" in text and not leaks(text, USER)


def test_every_place_for_the_report_failing_ends_in_the_temp_folder(tmp_path, monkeypatch):
    monkeypatch.setattr(problem_report.sysreport, "known_folder", lambda *a: str(tmp_path / "no" / "such" / "folder"))
    blocker = tmp_path / "blocker"
    blocker.write_text("file")
    monkeypatch.setattr(problem_report.os.path, "expanduser", lambda p: str(blocker))
    monkeypatch.setenv("NFL4_DATA_DIR", str(blocker / "data"))
    monkeypatch.setenv("TEMP", str(tmp_path))
    assert problem_report.desktop_folder() == str(tmp_path)


# ----- the whole program with its logs folder in a bad state -----

pytestmark_window = pytest.mark.window


def start(folder, monkeypatch, seconds=1.0):
    monkeypatch.setenv("NFL4_DATA_DIR", str(folder))
    monkeypatch.setenv("SDL_AUDIODRIVER", "dummy")
    monkeypatch.setattr(window_module.GameWindow, "show", lambda self: False)
    made = Made()
    monkeypatch.setattr(app, "create_speech", made)
    monkeypatch.setattr(window_module, "GameWindow", closing_after(seconds))
    return app.main(), made


def settings(folder):
    (folder / "settings.txt").write_text("# NFL Football 4 settings, format 1\n", encoding="utf-8")
    (folder / "sounds").mkdir(exist_ok=True)
    from wavmaker import sine, write
    write(folder / "sounds" / "foot0.wav", sine(400, 0.05, 11025), rate=11025)


@pytest.mark.window
def test_the_program_with_a_file_where_its_logs_folder_belongs_starts_plays_and_logs_to_the_temp_folder(tmp_path, monkeypatch):
    folder = tmp_path / "data"
    folder.mkdir()
    settings(folder)
    (folder / "logs").write_text("a file where the logs folder should be")
    monkeypatch.setattr(debuglog.tempfile, "gettempdir", lambda: str(tmp_path / "tmp"))
    code, made = start(folder, monkeypatch)
    assert code == 0 and texts.TITLE_SPOKEN in made.sapi.spoken()[:3]
    debuglog.flush(debuglog.REPORT_WAIT_SECONDS + 10)
    assert list((tmp_path / "tmp" / "nfl4-logs").glob("nfl4-2*.log")), "the fall back to the temp folder wrote nothing"


@pytest.mark.window
def test_the_program_with_a_full_disk_for_its_log_starts_speaks_and_closes(tmp_path, monkeypatch):
    folder = tmp_path / "data"
    folder.mkdir()
    settings(folder)

    def full(self, data):
        raise OSError(errno.ENOSPC, "No space left on device")
    monkeypatch.setattr(debuglog._Ring, "_raw", full)
    code, made = start(folder, monkeypatch)
    assert code == 0 and texts.TITLE_SPOKEN in made.sapi.spoken()[:3]


@pytest.mark.window
def test_the_program_with_ten_old_logs_one_of_them_locked_starts_and_keeps_the_newest_ten(tmp_path, monkeypatch):
    import filedamage
    folder = tmp_path / "data"
    logs = folder / "logs"
    logs.mkdir(parents=True)
    settings(folder)
    old = [logs / ("nfl4-2026010%d-000000.log" % n) for n in range(1, 10)] + [logs / "nfl4-20251231-000000.log"]
    for f in old:
        f.write_text("old")
    with filedamage.holding(old[-1]):                 # the oldest, which is the one to delete
        code, made = start(folder, monkeypatch)
    assert code == 0 and texts.TITLE_SPOKEN in made.sapi.spoken()[:3]
    debuglog.flush(debuglog.REPORT_WAIT_SECONDS + 10)
    assert len(list(logs.glob("nfl4-2*.log"))) <= 11


# ----- a long session -----

def test_a_long_session_keeps_the_caps_the_redaction_and_the_speed_of_the_game_thread(tmp_path):
    logs = tmp_path / "logs"
    path = begin(logs, half_bytes=256 * 1024)
    started = time.perf_counter()
    for n in range(60000):
        debuglog.event("game", "play", n=n, path="C:\\Users\\%s\\AppData\\x\\file%d.dat" % (USER, n), mail="%s@example.com" % USER,
                       text="Zoë and the account %s" % USER)
    elapsed = time.perf_counter() - started
    debuglog.flush(30)
    assert elapsed < 10, "the game thread waited for the log: %.1f s for 60,000 events" % elapsed
    total = 0
    for name in os.listdir(logs):
        total += os.path.getsize(logs / name)
    assert total <= 2 * 256 * 1024 + 64 * 1024, total
    text = written(path)
    assert not leaks(text, USER) and f"{USER}@" not in text
    assert text.count("system") >= 0 and "play" in text


# ----- S8.3 round 2: the lines added since the first S8.3 -----

def test_the_new_lines_with_paths_and_typed_names_are_redacted(tmp_path):
    """The lines of SZ.4 to SZ.8 and of this round that carry a path or the player's own text (rule 0.15: no account name, nothing private)."""
    path = begin(tmp_path / "logs")
    home = "C:\\Users\\%s" % USER
    debuglog.event("franchise", "calendar_missing", logging.INFO, season=2, year=2027, path=home + "\\AppData\\Local\\Programs\\NFL\\assets\\data\\schedule_2027.txt")
    debuglog.event("file", "teams_renamed", path=home + "\\AppData\\Roaming\\NFL Football 4\\customize\\teams.txt", t24="Commanders")
    debuglog.event("setting", "commentator_typed", typed="Jos\u00e9 " + USER, kept="Jose")
    debuglog.event("app", "screen_reader_found", logging.INFO, engine="NVDA", mode="auto")
    debuglog.event("app", "voice_list_skipped", logging.INFO, reason="the player chose the screen reader")
    debuglog.event("menu", "key", key="w", likely="Two Man", percent=22)
    logging.getLogger("nfl4.extras").info("first names: %d made-up players of franchise %s got a first name (D-131)", 1100, "20260101-000000")
    text = written(path)
    assert not leaks(text, USER) and f"{USER}@" not in text
    for name in ("calendar_missing", "teams_renamed", "commentator_typed", "screen_reader_found", "voice_list_skipped", "got a first name"):
        assert name in text, name


def test_a_franchise_season_on_the_real_calendar_logs_its_calendar_within_the_caps_and_without_the_account_name(tmp_path):
    from frrig import COACH_AND_TEAM, WANT_FRANCHISE, enter_until, franchise_rig, run_until
    logs = tmp_path / "logs"
    path = begin(logs, half_bytes=256 * 1024)
    rig = franchise_rig(tmp_path / "game", WANT_FRANCHISE + COACH_AND_TEAM, real_calendar=True, scores=lambda r: (28, 10),
                        policy=enter_until(lambda: rig.fstore is not None and rig.fstore.league is not None and rig.game.season.gtp == 19))
    run_until(rig)
    debuglog.flush(30)
    total = sum(os.path.getsize(logs / name) for name in os.listdir(logs))
    assert total <= 2 * 256 * 1024 + 64 * 1024, total
    text = written(path)
    assert not leaks(text, USER)
    assert "calendar" in text and "weeks=18" in text                                   # the calendar line names the 18 weeks and the bye
