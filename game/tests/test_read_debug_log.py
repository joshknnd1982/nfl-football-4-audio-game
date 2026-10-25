"""game/tools/read_debug_log.py: the reader of the debug log and the replay of a recorded game (playbook 7.11). This is inspired by Jim Kitchen."""
import importlib.util
import logging
import os
import random
import sys
from pathlib import Path

from nfl4.data import debuglog, problem_report, sysreport
from nfl4.data.settings import Settings
from pagrig import make_rig, play
from test_debuglog import begin, written
from test_pag_games import lively_policy

TOOL = Path(__file__).resolve().parent.parent / "tools" / "read_debug_log.py"
spec = importlib.util.spec_from_file_location("read_debug_log", TOOL)
reader = importlib.util.module_from_spec(spec)
sys.modules["read_debug_log"] = reader
spec.loader.exec_module(reader)


def a_log_with_a_fault(tmp_path):
    path = debuglog.start("detailed", str(tmp_path / "logs"))
    report = debuglog.report()
    sysreport.build(report, args=[], settings=Settings.defaults(), speech=None, speech_settings=Settings.defaults().speech)
    debuglog.report_done()
    debuglog.event("speech", "request", role="announcer", backend="SAPI 5", text="hello")
    debuglog.event("perf", "SLOW", logging.INFO, name="load", ms=900)
    logging.getLogger("nfl4.speech").warning("SAPI 5 speak failed: boom")
    try:
        1 / 0
    except ZeroDivisionError:
        logging.getLogger("nfl4.game").exception("a caught error")
    debuglog.event("app", "after")
    debuglog.flush()
    return path


def test_the_reader_prints_the_setup_the_problems_the_context_and_the_seed_in_that_order(tmp_path):
    path = a_log_with_a_fault(tmp_path)
    debuglog.shutdown("test")
    log = reader.load(path)
    text = reader.report(log)
    order = [text.index(h) for h in ("== setup", "== warnings, errors, slow steps", "== the 40 lines before the first error",
                                      "== the last 40 lines", "== settings and customization files", "== random seeds")]
    assert order == sorted(order)
    assert "SAPI 5 speak failed: boom" in text and "SLOW" in text and "ZeroDivisionError" in text
    assert "by backend: SAPI 5 problems 1, SAPI 5 spoke 1" in text and "last event: closed" in text
    assert len(reader.setup_lines(log)) == 10


def test_the_reader_opens_a_problem_report_zip_and_a_logs_folder(tmp_path, monkeypatch):
    monkeypatch.setenv("NFL4_DATA_DIR", str(tmp_path / "data"))
    path = a_log_with_a_fault(tmp_path)
    debuglog.shutdown("test")
    import shutil
    (tmp_path / "data" / "logs").mkdir(parents=True)
    shutil.copy(path, tmp_path / "data" / "logs")
    archive = problem_report.make(False, str(tmp_path / "out"), system_kwargs=dict(args=[], settings=None))
    from_zip = reader.load(archive)
    from_folder = reader.load(str(tmp_path / "logs"))
    assert any(e.name == "after" for e in from_zip.events) and any(e.name == "after" for e in from_folder.events)
    assert from_folder.report["game"] == "NFL Football 4"


def test_a_game_recorded_at_the_trace_level_replays_from_its_own_log_to_the_same_speech(tmp_path):
    path = begin(tmp_path / "logs", "trace")
    rig = make_rig(tmp_path / "rig", rng=random.Random(2034))
    rig.rnd.seed = 2034
    rig.keys.policy = lively_policy(rig, 3034)
    rig.rnd.mark("game_start", tn1=1, tn2=1, tn3=2, tn4=3, vtrnt=2)
    play(rig)
    debuglog.event("app", "game_end")
    debuglog.flush(30)
    log = reader.load(path)
    assert sum(1 for e in log.events if e.name == "pump") > 20 and sum(1 for e in log.events if e.name == "draw") > 100
    verdict = reader.replay(log, 1, str(tmp_path / "replay"))
    assert verdict["stopped"] == "" and verdict["identical"], verdict
    assert verdict["replayed_speech"] == verdict["logged_speech"] > 50 and "recorded draws" in verdict["mode"]


def test_a_game_recorded_without_trace_replays_from_its_seed_and_the_draw_count(tmp_path):
    path = begin(tmp_path / "logs", "detailed")
    rig = make_rig(tmp_path / "rig", rng=random.Random(77))
    rig.rnd.seed = 77
    rig.keys.policy = lively_policy(rig, 5)
    rig.rnd.mark("game_start", tn1=1, tn2=1, tn3=2, tn4=3, vtrnt=2)
    play(rig)
    debuglog.event("app", "game_end")
    debuglog.flush(30)
    verdict = reader.replay(reader.load(path), 1, str(tmp_path / "replay"))
    assert verdict["identical"] and "seed 77" in verdict["mode"], verdict
