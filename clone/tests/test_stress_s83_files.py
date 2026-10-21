"""The 7.10 damage matrix through the whole program (S8.3; GAP_REGISTER G-A6, G-F5; playbook 7.10 last bullet). This is inspired by Jim Kitchen.

The store and customization tests damage one file family at a time below the program (tests/test_files_store.py, test_customize_damage.py,
test_sx9_league_damage.py). Here the real program (app.main(): the real window and game thread, fake speech) is started on a data folder in which
ONE file has been damaged in each way of the matrix: deleted, its folder gone, emptied, cut in half, random bytes, another encoding, huge,
binary zeros, a bad line in the middle, no header, read-only, held open by another program, a folder where the file should be. After each the
program starts, speaks its welcome, closes with 0 and its launch log ends with `closed`, and never writes a traceback of an unexpected kind.
"""
import os
import re
import shutil
import threading
import time

import pytest

import filedamage
import nfl4.app as app
import nfl4.ui.window as window_module
from nfl4.game import texts
from test_app_startup import Made, a_season_in, closing_after, launch_log, write_settings
from wavmaker import sine, write

pytestmark = pytest.mark.window

SOUNDS = "sounds"
# a caught error that is the file system's (a folder where a file belongs, a sharing violation) is logged at ERROR with its traceback and is
# fine; one of these is a bug in the program that a damaged file reached
PROGRAMMING_ERRORS = re.compile(r"(TypeError|AttributeError|KeyError|IndexError|NameError|UnboundLocalError|ValueError|AssertionError|"
                                r"RecursionError|ZeroDivisionError|UnicodeError|UnicodeDecodeError|UnicodeEncodeError|OverflowError|MemoryError)")


@pytest.fixture(autouse=True)
def sound_on_the_dummy_driver(monkeypatch):
    monkeypatch.setenv("SDL_AUDIODRIVER", "dummy")


@pytest.fixture(autouse=True)
def window_stays_in_the_background(monkeypatch):
    monkeypatch.setattr(window_module.GameWindow, "show", lambda self: False)


def closing_when_spoken(made, after=0.4, limit=20.0):
    """The player closes the window `after` seconds after the program first speaks (at most `limit` seconds from the start). The intro of
    3.4 s plays on SDL's dummy driver in real time and ends anywhere between 3.4 and 8 s on a busy PC (B-X103), so a fixed time is a flaky
    test; the welcome is the program's first words, whenever they come."""
    real = window_module.GameWindow

    class Closing(real):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            threading.Thread(target=self.watch, daemon=True).start()

        def watch(self):
            began = time.monotonic()
            while not made.sapi.spoken() and time.monotonic() - began < limit:
                time.sleep(0.02)
            time.sleep(after)
            self.close()
    return Closing


def start(folder, monkeypatch, seconds=None):
    monkeypatch.setenv("NFL4_DATA_DIR", str(folder))
    made = Made()
    monkeypatch.setattr(app, "create_speech", made)
    monkeypatch.setattr(window_module, "GameWindow", closing_after(seconds) if seconds else closing_when_spoken(made))
    code = app.main()
    return code, made


@pytest.fixture(scope="module")
def template(tmp_path_factory):
    """A data folder as a player's looks after some play: settings, the sounds folder and its sounds.txt, every customization file, a season
    (coach, schedule, week 5, records), a log and a leftover of the crash guard are not in it (those are damaged by the tests that need them)."""
    folder = tmp_path_factory.mktemp("template")
    mp = pytest.MonkeyPatch()
    try:
        mp.setenv("SDL_AUDIODRIVER", "dummy")
        mp.setattr(window_module.GameWindow, "show", lambda self: False)
        write_settings(folder, [])                                          # a new player's rules: the N. F. L. rules, so every extra file is made
        (folder / SOUNDS).mkdir()
        write(folder / SOUNDS / "foot0.wav", sine(400, 0.05, 11025), rate=11025)   # a short intro in place of the 3.4 s one (test_app_startup)
        a_season_in(folder, gtp=5)
        (folder / "footballlog.txt").write_bytes(b"an earlier week\r\n")
        code, _ = start(folder, mp, 1.5)
        assert code == 0
    finally:
        mp.undo()
    return folder


def files_of(folder):
    out = []
    for root, _, names in os.walk(folder):
        if os.path.basename(root) == "logs":
            continue
        for name in names:
            path = os.path.relpath(os.path.join(root, name), folder).replace("\\", "/")
            if ".damaged" in name or path.startswith("logs/"):
                continue
            out.append(path)
    return sorted(out)


def test_the_template_has_every_file_the_matrix_damages_and_the_matrix_names_every_file_there_is(template):
    names = set(files_of(template))
    assert set(targets()) - {"football.sav"} == names, (sorted(names - set(targets())), sorted(set(targets()) - names))


def targets():
    """The files of the template, named here because the parameters are made before any program runs (the names are the program's own:
    data/files/store.py, data/customize.py, data/settingsfile.py, audio/soundsconfig.py). test_the_template_has_the_files lists them."""
    customize = ["customize/" + name + ".txt" for name in ("banter", "divisions", "injuries", "news", "penalties", "remarks", "surnames", "teams")]
    playbooks = ["customize/playbooks/" + name + ".txt" for name in ("plays", "styles", "team_styles", "favourites")]   # SX.10c
    return (["settings.txt", "sounds/sounds.txt", "sounds/foot0.wav", "footbal1.dat", "footbal2.dat", "footbal3.dat", "football.gtp",
             "footballlog.txt", "commercials/About commercials.txt", "football.sav"] + customize + playbooks)


DAMAGES = [kind for kind in filedamage.BYTE_DAMAGES if kind != "newer_format"] + ["deleted", "folder_gone", "read_only", "held_open",
                                                                                  "a_folder_in_its_place"]


def damage(folder, relative, kind):
    path = folder / relative
    if not path.exists():
        pytest.skip(f"{relative} is not made in this configuration")
    if kind in filedamage.BYTE_DAMAGES:
        filedamage.apply(kind, path)
        return None
    if kind == "deleted":
        path.unlink()
    elif kind == "folder_gone":
        if path.parent == folder:
            pytest.skip("the file is in the data folder itself")
        shutil.rmtree(path.parent)
    elif kind == "a_folder_in_its_place":
        path.unlink()
        path.mkdir()
    elif kind == "read_only":
        return filedamage.read_only(path)
    elif kind == "held_open":
        return filedamage.holding(path)
    return None


@pytest.mark.parametrize("kind", DAMAGES)
@pytest.mark.parametrize("relative", targets())
def test_one_damaged_file_and_the_program_still_starts_speaks_and_closes(template, tmp_path, monkeypatch, relative, kind):
    folder = tmp_path / "data"
    shutil.copytree(template, folder)
    if relative == "football.sav":                                    # a game saved in the middle: the program takes it at the start and plays it on
        from nfl4.data.files.store import FileProgramStore
        from test_files_store import a_game
        assert FileProgramStore(str(folder), str(folder / "customize")).save_game(a_game())
    context = damage(folder, relative, kind)
    if context is None:
        code, made = start(folder, monkeypatch)
    else:
        with context:
            code, made = start(folder, monkeypatch)
    assert code == 0
    spoken = made.sapi.spoken()
    assert texts.TITLE_SPOKEN in spoken[:3], spoken[:3]                  # a first start (settings.txt gone) begins with a blank, then the welcome
    log = launch_log(folder)
    assert "NFL Football 4 clone closed" in log
    assert not [line for line in log.splitlines() if "Traceback" in line and PROGRAMMING_ERRORS.search(line)], "a programming error was logged"
    if os.path.isfile(folder / "settings.txt"):
        assert os.path.getsize(folder / "settings.txt") > 0
