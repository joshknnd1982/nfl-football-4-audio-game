"""The Franchise's league.sav damaged under the whole program (S8.3 round 2; nfl4 only, rule 0.13; playbook 7.10). This is inspired by Jim Kitchen.

The start-up menu (SX.14) reads what is saved before anything else, the franchise too, so a damaged league.sav is met at the very start. The store's
own tests damage it below the program (test_sx9_league_damage.py, test_fr_store.py). Here the real program (app.main(): the real window and game
thread, fake speech) starts on a data folder whose franchise was written by the program (format 13, the real calendar, week 3) and then damaged in
each way of the matrix, or replaced by a file of format 11 or 12 (the migrations of SZ.8 and D-131) or of a newer format. Each time the program starts,
speaks its welcome, closes with 0, its launch log ends with `closed`, no programming error is logged, and the player's franchise file is either
used, kept aside with its copy, or left untouched (a newer format) -- never lost.
"""
import json
import os
import shutil

import pytest
import filedamage
from frrig import COACH_AND_TEAM, WANT_FRANCHISE, enter_until, franchise_rig, run_until
from test_stress_s83_files import (DAMAGES, PROGRAMMING_ERRORS, sound_on_the_dummy_driver, start, template,  # noqa: F401 (fixtures)
                                   window_stays_in_the_background)
from test_app_startup import launch_log

from nfl4.extras.franchise import data as D
from nfl4.extras.franchise import first_names as FN
from nfl4.game import texts

pytestmark = pytest.mark.window


@pytest.fixture(scope="module")
def franchise_files(tmp_path_factory):
    """The files of a franchise in week 3 of the real calendar, as the program writes them."""
    folder = tmp_path_factory.mktemp("franchise")
    rig = franchise_rig(folder, WANT_FRANCHISE + COACH_AND_TEAM, real_calendar=True, scores=lambda r: (28, 10),
                        policy=enter_until(lambda: rig.fstore is not None and rig.fstore.league is not None and rig.game.season.gtp == 3))
    run_until(rig)
    return dict(rig.files.data)


def older(raw: bytes, version: int) -> bytes:
    data = json.loads(raw.decode("utf-8"))
    lid = data["league_id"]
    for row in data["players"]:
        surname = FN.surname_of(lid, row[1])
        if surname is not None:
            row[1] = surname                                       # the bare drawn surnames of 0.12.0 and older
    data["format"] = version
    if version < 12:
        data.pop("calendar", None)
    return json.dumps(data).encode("utf-8")


KINDS = ["intact"] + DAMAGES + ["format_11", "format_12", "newer_format_14", "previous_damaged_too"]


@pytest.mark.parametrize("kind", KINDS)
def test_a_damaged_franchise_file_and_the_program_still_starts_speaks_and_closes(template, franchise_files, tmp_path, monkeypatch, kind):
    folder = tmp_path / "data"
    shutil.copytree(template, folder)
    home = folder / D.FOLDER
    home.mkdir()
    for name, raw in franchise_files.items():
        (home / name).write_bytes(raw)
    league = home / D.LEAGUE_FILE
    before = league.read_bytes()
    context = None
    if kind == "format_11":
        league.write_bytes(older(before, 11))
    elif kind == "format_12":
        league.write_bytes(older(before, 12))
    elif kind == "newer_format_14":
        league.write_bytes(before.replace(b'"format":%d' % D.FORMAT, b'"format":%d' % (D.FORMAT + 1), 1))
    elif kind == "previous_damaged_too":
        filedamage.apply("cut_in_half", league)
        if (home / D.PREVIOUS_FILE).exists():
            filedamage.apply("random_bytes", home / D.PREVIOUS_FILE)
    elif kind in filedamage.BYTE_DAMAGES:
        filedamage.apply(kind, league)
    elif kind == "deleted":
        league.unlink()
    elif kind == "folder_gone":
        shutil.rmtree(home)
    elif kind == "a_folder_in_its_place":
        league.unlink()
        league.mkdir()
    elif kind == "read_only":
        context = filedamage.read_only(league)
    elif kind == "held_open":
        context = filedamage.holding(league)
    damaged = league.read_bytes() if league.is_file() and kind != "held_open" else None
    if context is None:
        code, made = start(folder, monkeypatch)
    else:
        with context:
            code, made = start(folder, monkeypatch)
    assert code == 0
    assert texts.TITLE_SPOKEN in made.sapi.spoken()[:3]
    log = launch_log(folder)
    assert "NFL Football 4 clone closed" in log
    assert not [line for line in log.splitlines() if "Traceback" in line and PROGRAMMING_ERRORS.search(line)], "a programming error was logged"
    if kind in ("intact", "format_11", "format_12"):
        assert any("franchise" in t.lower() for t in made.sapi.spoken()), made.sapi.spoken()[:8]   # the start-up menu read it and names it
    if kind == "newer_format_14":
        assert league.read_bytes() == damaged                                      # a newer version's file is never touched
    if damaged is not None and league.is_file() and league.read_bytes() != damaged:
        kept = [n for n in os.listdir(home) if n != D.LEAGUE_FILE]
        assert kept, "the damaged franchise was replaced and no copy of it was kept"
