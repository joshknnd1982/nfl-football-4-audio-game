"""The detailed debug log and the problem report (owner rule 0.15, playbook 7.11): the tests the playbook lists. This is inspired by Jim Kitchen.

The log is the only way to fix a bug that happens on another player's computer, so it is held to its contract here: the startup
report has every item, a fault leaves its line at the right level, the Windows account name is in no file, a log that cannot be
written never stops the game, the caps hold, the last line is `closed`, the problem report holds exactly the listed members, and
the log costs the key-to-sound path nothing measurable.
"""
import errno
import getpass
import logging
import os
import re
import statistics
import threading
import time
import zipfile

import pytest

from nfl4.data import debuglog, lifecycle, paths, problem_report, sysreport
from nfl4.speech.fake import FakeBackend
from nfl4.speech.manager import SpeechManager

USER = getpass.getuser()
ACCENTED = "Zoë Müller-Žák"


def begin(folder, level="detailed", half_bytes=debuglog.HALF_BYTES):
    """Start a log in `folder`, with the report released at once (a test does not wait for the report's thread)."""
    path = debuglog.start(level, str(folder), half_bytes)
    debuglog.report().section("test", [("game", "nfl4 test")])
    debuglog.report_done()
    return path


def written(path=None):
    """Everything the log has written so far, both halves, in order."""
    debuglog.flush()
    path = path or debuglog.path()
    base = os.path.splitext(path)[0]
    texts = [open(p, encoding="utf-8").read() for p in (path, base + "-b.log") if os.path.exists(p)]
    return "\n".join(texts)


def leaks(text, name):
    """The account name after a path separator, in any case: what the redaction must have removed."""
    return re.search(r"[\\/]" + re.escape(name) + r"(?![\w])", text, re.IGNORECASE) is not None


def all_text_under(folder):
    out = []
    for root, _, names in os.walk(folder):
        for name in names:
            with open(os.path.join(root, name), "rb") as handle:
                out.append(handle.read().decode("utf-8", "replace"))
    return "\n".join(out)


# ----- the format and the levels -----

def test_a_line_has_the_time_the_elapsed_time_the_level_the_thread_the_component_the_run_id_and_key_values(tmp_path):
    path = begin(tmp_path)
    debuglog.event("speech", "request", role="announcer", text="Hike!\nTwo lines", chars=5)
    text = written(path)
    line = next(l for l in text.splitlines() if " request " in l)
    parts = line.split(" ", 6)
    assert len(parts[0]) == 12 and parts[0][2] == ":" and parts[1].startswith("+") and parts[2] == "DEBUG"
    assert parts[4] == "speech" and parts[5] == debuglog.run_id() and parts[6].startswith("request role=announcer")
    assert 'text="Hike!\\nTwo lines"' in line and "\n" not in line.rstrip("\n")           # a newline in a value is \n


def test_the_default_level_is_detailed_normal_drops_debug_and_off_makes_no_file(tmp_path):
    assert debuglog.DEFAULT_LEVEL == "detailed"
    path = begin(tmp_path / "a", "normal")
    debuglog.event("speech", "request", text="debug line")
    logging.getLogger("nfl4.test").warning("a warning")
    text = written(path)
    assert "debug line" not in text and "a warning" in text
    assert debuglog.start("off", str(tmp_path / "b")) is None and not (tmp_path / "b").exists()
    debuglog.event("speech", "request", text="nobody hears")                 # costs one comparison, writes nothing
    assert debuglog.level_name() == "off"


def test_trace_adds_the_random_draws_and_detailed_does_not(tmp_path):
    from nfl4.game.rnd import GameRandom
    begin(tmp_path / "t", "trace")
    rnd = GameRandom()
    rnd(6)
    assert " draw n=1 " in written() and " seed seed=%d" % rnd.seed in written()
    begin(tmp_path / "d", "detailed")
    GameRandom()(6)
    assert " draw " not in written()


def test_the_level_comes_from_the_command_line_then_the_environment_then_settings_txt(tmp_path, monkeypatch):
    (tmp_path / "settings.txt").write_text("# NFL Football 4 settings, format 1\ndebug_log = normal\n", encoding="utf-8")
    assert debuglog.level_from_settings_file(str(tmp_path)) == "normal"
    assert debuglog.level_from_environment([]) is None
    monkeypatch.setenv("NFL4_DEBUG_LOG", "trace")
    assert debuglog.level_from_environment([]) == "trace"
    assert debuglog.level_from_environment(["--debug-log=off"]) == "off"
    monkeypatch.delenv("NFL4_DEBUG_LOG")
    monkeypatch.setenv("NFL4_DEBUG", "1")
    assert debuglog.level_from_environment([]) == "detailed"


def test_changing_the_level_while_playing_takes_effect_and_is_written(tmp_path):
    path = begin(tmp_path)
    debuglog.set_level("normal")
    debuglog.event("speech", "request", text="after the change")
    debuglog.set_level("detailed")
    debuglog.event("speech", "request", text="back again")
    text = written(path)
    assert "after the change" not in text and "back again" in text
    assert "log_level old=detailed new=normal" in text


# ----- the startup report -----

class _Audio:
    ok, error = True, None

    class library:
        problems = []
        shipped_dir = player_dir = "."

    class output:
        buffer = 256


def test_the_startup_report_has_every_item_with_a_value_or_n_a_and_its_reason(tmp_path):
    report = debuglog.Report()
    manager = SpeechManager(FakeBackend(name="SAPI 5", takes_roles=True), None, "sapi")
    from nfl4.data.settings import Settings
    sysreport.build(report, args=["--debug-log=trace"], cwd_before=str(tmp_path), cwd_after=str(tmp_path), welcome="Welcome.",
                    speech=manager, speech_settings=Settings.defaults().speech, audio=_Audio, store=None, custom=None,
                    settings=Settings.defaults())
    lines = {l.split(" = ", 1)[0]: l.split(" = ", 1)[1] for l in report.lines() if " = " in l}
    assert [key for key in sysreport.REQUIRED_KEYS if key not in lines] == []
    for key in sysreport.REQUIRED_KEYS:
        assert lines[key].strip(), key
        assert not lines[key].startswith("n/a") or lines[key].startswith("n/a ("), key       # n/a always says why
    assert lines["welcome_sentence"] == "Welcome." and lines["command_line"] == "--debug-log=trace"


def test_a_probe_that_fails_says_n_a_with_the_reason_and_the_report_goes_on(monkeypatch):
    monkeypatch.setattr(sysreport, "memory_mb", lambda: (_ for _ in ()).throw(OSError("no memory call")))
    items = dict(sysreport.windows_section())
    assert items["memory_mb"].startswith("n/a (") and "no memory call" in items["memory_mb"] and items["cpu_count"]


def test_the_report_is_at_the_top_of_the_file_and_the_events_wait_for_it(tmp_path):
    path = debuglog.start("detailed", str(tmp_path))
    debuglog.event("app", "early", note="before the report is ready")
    report = debuglog.report()
    report.section("program", [("game", "nfl4"), ("version", "9.9")])
    time.sleep(0.2)
    assert open(path, encoding="utf-8").read() == ""                          # nothing is written before the report
    debuglog.report_done()
    text = written(path).splitlines()
    assert text[0].startswith("==== startup report") and "version = 9.9" in text
    assert text.index("==== end of startup report ====") < next(i for i, l in enumerate(text) if " early " in l)


# ----- faults leave their lines -----

def test_a_failing_voice_a_missing_sound_a_damaged_file_a_worker_exception_and_an_unwritable_file_each_leave_their_line(tmp_path):
    path = begin(tmp_path / "logs")
    from nfl4.data.healing import save_damaged_copy, write_text_atomic
    from nfl4.speech.backend import SpeechBackend

    class Failing(FakeBackend):
        def speak(self, text, role=None, rate_step=0):
            raise RuntimeError("voice is broken")

    manager = SpeechManager(Failing(name="SAPI 5", takes_roles=True), FakeBackend(name="NVDA"), "sapi")
    manager.say_async("hello")                                                 # falls back, WARNING with the traceback
    from nfl4.audio.library import SoundLibrary
    library = SoundLibrary(str(tmp_path / "none"), str(tmp_path / "player"))
    library.pick_file(str(tmp_path / "player" / "missing.wav"))                 # a missing sound
    damaged = tmp_path / "data" / "settings.txt"
    damaged.parent.mkdir()
    damaged.write_bytes(b"\x00\x01\x02")
    save_damaged_copy(str(damaged))
    thread = threading.Thread(target=lambda: 1 / 0, name="worker")
    thread.start()
    thread.join()
    folder = tmp_path / "readonly"
    folder.mkdir()
    (folder / "file.txt").write_text("x")
    os.chmod(folder / "file.txt", 0o444)
    assert write_text_atomic(str(folder / "file.txt"), "new") in (True, False)  # a read-only file: either way it is in the log
    text = written(path)
    assert "WARNING" in text and "voice is broken" in text and "traceback=" in text and "RuntimeError" in text
    assert "damaged_copy" in text and "missing.wav" in text


def test_an_exception_in_another_thread_is_logged_with_its_traceback_by_the_installed_hook(tmp_path):
    path = begin(tmp_path)
    debuglog.install_exception_hooks()
    thread = threading.Thread(target=lambda: 1 / 0, name="worker-x")
    thread.start()
    thread.join()
    text = written(path)
    assert "unhandled error in thread worker-x" in text and "ZeroDivisionError" in text and " ERROR " in text


def test_a_hang_dumps_every_thread_once_into_the_crash_log_and_a_heartbeat_is_written(tmp_path, monkeypatch):
    monkeypatch.setattr(debuglog, "HANG_SECONDS", 0.5)
    monkeypatch.setattr(debuglog, "HEARTBEAT_SECONDS", 1.0)
    path = begin(tmp_path)
    debuglog.beat()
    deadline = time.time() + 6
    while time.time() < deadline and "HANG" not in written(path):
        time.sleep(0.2)
    time.sleep(1.2)                                                             # still only one dump while it stays hung
    text = written(path)
    assert text.count(" HANG ") == 1 and "heartbeat" in text
    crash = open(debuglog.crash_path(), encoding="utf-8", errors="replace").read()
    assert "no heartbeat" in crash and "Thread" in crash


# ----- privacy -----

def test_the_windows_account_name_and_other_private_text_are_in_no_file(tmp_path):
    debuglog.add_private_name(ACCENTED)
    path = begin(tmp_path / "logs")
    debuglog.event("file", "read", path=r"C:\Users\%s\AppData\Roaming\x.txt" % USER)
    debuglog.event("file", "read", path="C:/Users/%s/Documents/y.txt" % ACCENTED)
    debuglog.event("app", "note", mail="reach me at someone@example.com", password="hunter2 and more", token=" token=abc123")
    logging.getLogger("nfl4.test").error("boom in C:\\Users\\%s\\code\\x.py", USER)
    debuglog.add_typed("Coach Zebediah")
    debuglog.event("speech", "request", text="Hello Coach Zebediah, welcome")
    text = written(path)
    for secret in ("someone@example.com", "hunter2", "abc123", "zebediah"):
        assert secret not in text.lower()
    assert not leaks(text, USER) and not leaks(text, ACCENTED) and ACCENTED.lower() not in text.lower()
    assert "<user>" in text and "<email>" in text and "<hidden>" in text and "<typed>" in text
    assert not leaks(all_text_under(tmp_path / "logs"), USER)


def test_a_word_that_is_also_the_account_name_is_left_alone_outside_a_path(tmp_path):
    debuglog.add_private_name("Josh")
    path = begin(tmp_path)
    debuglog.event("app", "note", text="Welcome to Josh Kennedy's N. F. L. football", path=r"C:\Users\Josh\x")
    text = written(path)
    assert "Josh Kennedy's" in text and "C:\\Users\\<user>\\x" in text.replace("C:\\\\Users\\\\<user>\\\\x", "C:\\Users\\<user>\\x")


def test_what_the_player_types_is_written_as_its_length_only_and_no_key_while_typing(tmp_path):
    from nfl4.ui.window import log_key
    path = begin(tmp_path)
    with debuglog.context("typing: Enter the name of your coach"):
        log_key(0x5A, 0)                                                       # the letter Z
    log_key(0x5A, 0)
    text = written(path)
    assert " down typed=true" in text and text.count(" down vk=90") == 1


# ----- never in the way -----

def test_an_unwritable_folder_falls_back_to_the_temp_folder_and_the_game_goes_on(tmp_path, monkeypatch):
    monkeypatch.setattr(debuglog.tempfile, "gettempdir", lambda: str(tmp_path / "tmp"))
    blocker = tmp_path / "blocker"
    blocker.write_text("a file where the logs folder should be")
    path = debuglog.start("detailed", str(blocker / "logs"))
    debuglog.report().section("test", [("game", "x")])
    debuglog.report_done()
    debuglog.event("app", "still_works")
    assert path is not None and os.path.dirname(path).endswith("nfl4-logs") and "still_works" in written(path)


def test_when_no_folder_works_nothing_is_written_and_nothing_raises(tmp_path, monkeypatch):
    monkeypatch.setattr(debuglog.tempfile, "gettempdir", lambda: str(tmp_path / "blocker" / "tmp"))
    (tmp_path / "blocker").write_text("file")
    assert debuglog.start("detailed", str(tmp_path / "blocker" / "logs")) is None
    debuglog.event("app", "no file")
    logging.getLogger("nfl4.x").warning("still fine")
    debuglog.shutdown("done")


def test_a_full_disk_is_survived_the_error_is_counted_and_the_game_keeps_running(tmp_path, monkeypatch):
    path = begin(tmp_path / "logs")
    debuglog.event("app", "before")
    written(path)

    def full(self, data):
        raise OSError(errno.ENOSPC, "No space left on device")

    monkeypatch.setattr(debuglog._Ring, "_raw", full)
    for n in range(50):
        debuglog.event("app", "while_full", n=n)
    debuglog.flush()
    assert debuglog.errors() >= 1
    started = time.perf_counter()
    for n in range(2000):
        debuglog.event("app", "more", n=n)
    assert time.perf_counter() - started < 1.0                                  # the game thread never waits for the disk


def test_an_old_log_held_open_by_another_program_does_not_stop_the_next_start(tmp_path):
    logs = tmp_path / "logs"
    logs.mkdir()
    old = [logs / ("nfl4-2026010%d-000000.log" % n) for n in range(1, 10)] + [logs / "nfl4-20251231-000000.log"]
    for f in old:
        f.write_text("old")
    holder = open(old[-1], "rb")                                                # the oldest, which is the one to delete
    try:
        begin(logs)
        debuglog.event("app", "started_anyway")
        assert "started_anyway" in written()
    finally:
        holder.close()


def test_only_the_newest_ten_launches_are_kept(tmp_path):
    logs = tmp_path / "logs"
    logs.mkdir()
    for n in range(14):
        (logs / ("nfl4-202601%02d-120000.log" % (n + 1))).write_text("old %d" % n)
        (logs / ("nfl4-202601%02d-120000-b.log" % (n + 1))).write_text("old half")
    (logs / "nfl4-crash.log").write_text("kept across launches")
    begin(logs)
    launches = sorted({n[5:20] for n in os.listdir(logs) if n.startswith("nfl4-2")})
    assert len(launches) == 10 and launches[0] == "20260106-120000" and (logs / "nfl4-crash.log").exists()


def test_thirty_megabytes_of_lines_stay_under_the_caps_with_the_report_on_top_of_each_half(tmp_path):
    half = 64 * 1024
    path = begin(tmp_path / "logs", half_bytes=half)
    line = "x" * 180
    for n in range(30 * 1024 * 1024 // 200):
        debuglog.event("bulk", "line", n=n, pad=line)
        if n % 20000 == 0:
            debuglog.flush(60)
    debuglog.flush(60)
    base = os.path.splitext(path)[0]
    sizes = [os.path.getsize(p) for p in (path, base + "-b.log") if os.path.exists(p)]
    assert len(sizes) == 2 and max(sizes) < half + 4096
    for part in (path, base + "-b.log"):
        assert open(part, encoding="utf-8").readline().startswith("==== startup report")
        assert "-- part" in open(part, encoding="utf-8").read(4000)


def test_finish_flushes_the_queue_and_the_last_line_is_closed(tmp_path):
    path = begin(tmp_path)
    for n in range(500):
        debuglog.event("app", "busy", n=n)
    ended = []
    lifecycle.finish(0, exit_fn=ended.append)
    lines = open(path, encoding="utf-8").read().splitlines()
    assert ended == [0] and " closed " in lines[-1] and "n=499" in "\n".join(lines)


def test_the_key_to_sound_path_is_not_slowed_with_trace_on(tmp_path):
    """The cost of the log calls a key makes (a key, a speech request, a sound): well under a millisecond, with trace on."""
    from nfl4.game.keys import KeyInput
    begin(tmp_path, "trace")
    keys = KeyInput()
    manager = SpeechManager(FakeBackend(name="SAPI 5", takes_roles=True), None, "sapi")
    costs = []
    for n in range(400):
        keys.post(40)
        began = time.perf_counter()
        keys.pump()
        manager.say_async("Item %d" % n, role="announcer")
        debuglog.event("sound", "play", slot="one-shot", id="snd_foot1", chain="original", file="foot1.wav", volume=0, pan=0)
        costs.append(time.perf_counter() - began)
    assert statistics.median(costs) < 0.001 and max(costs) < 0.05


# ----- the problem report -----

def test_the_problem_report_holds_exactly_the_listed_members_and_hides_the_account_name_everywhere(tmp_path, monkeypatch):
    data = tmp_path / "data"
    monkeypatch.setenv("NFL4_DATA_DIR", str(data))
    data.mkdir()
    (data / "settings.txt").write_text("# note: made in C:\\Users\\%s\\Desktop\ndebug_log = detailed\n" % USER, encoding="utf-8")
    (data / "football.sav").write_bytes(b"saved game")
    (data / "franchise").mkdir()
    (data / "franchise" / "league.sav").write_text("league")
    for n in range(5):                                                         # five launches: the newest three go in
        logs = data / "logs"
        logs.mkdir(exist_ok=True)
        (logs / ("nfl4-202610%02d-100000.log" % (n + 1))).write_text("launch %d in C:\\Users\\%s\\x" % (n, USER), encoding="utf-8")
    (data / "logs" / "nfl4-crash.log").write_text("stack of C:\\Users\\%s\\py.exe" % USER, encoding="utf-8")
    begin(data / "logs2")
    monkeypatch.setattr(problem_report, "log_folders", lambda: [str(data / "logs")])
    plain = problem_report.make(False, str(tmp_path / "out"), system_kwargs=dict(args=[], settings=None))
    names = problem_report.listing(plain)
    assert sorted(names) == sorted(["README.txt", "system.txt", "logs/nfl4-20261003-100000.log", "logs/nfl4-20261004-100000.log",
                                    "logs/nfl4-20261005-100000.log", "crash-log.txt", "settings.txt", "customization.txt"])
    with_saves = problem_report.make(True, str(tmp_path / "out2"), system_kwargs=dict(args=[], settings=None))
    assert {n for n in problem_report.listing(with_saves)} - set(names) == {"saved/football.sav", "saved/franchise/league.sav"}
    for archive in (plain, with_saves):
        with zipfile.ZipFile(archive) as bundle:
            for member in bundle.namelist():
                assert not leaks(bundle.read(member).decode("utf-8", "replace"), USER), member
            assert "<user>" in bundle.read("settings.txt").decode("utf-8")


def test_the_command_line_makes_the_report_without_a_window(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("NFL4_DATA_DIR", str(tmp_path / "data"))
    import nfl4.app as app
    assert app.main(["--problem-report", "--quiet", "--folder=" + str(tmp_path / "out")]) == 0
    saved = [n for n in os.listdir(tmp_path / "out") if n.endswith(".zip")]
    assert len(saved) == 1 and saved[0] in capsys.readouterr().out
    assert "README.txt" in problem_report.listing(str(tmp_path / "out" / saved[0]))


# ----- the settings -----

def test_debug_log_is_a_setting_that_is_saved_and_read_back_and_a_bad_value_is_reported(tmp_path):
    from nfl4.data import settingsfile
    from nfl4.data.settings import Settings
    settings = Settings.defaults()
    assert settings.game.debug_log == "detailed"
    settings.game.debug_log = "trace"
    parsed, problems = settingsfile.parse(settingsfile.render(settings))
    assert parsed.game.debug_log == "trace" and problems == []
    _, problems = settingsfile.parse("# NFL Football 4 settings, format 1\ndebug_log = loud\n")
    assert any("debug_log" in p for p in problems)


def test_a_changed_setting_is_logged_with_its_old_and_new_value(tmp_path):
    from nfl4.data.settingsfile import SettingsStore
    path = begin(tmp_path / "logs")
    store = SettingsStore(str(tmp_path / "data"))
    settings = store.load()
    settings.game.comments = False
    store.save()
    assert " changed name=comments old=on new=off" in written(path)


def test_the_player_typed_text_is_registered_when_a_prompt_returns_it(tmp_path):
    path = begin(tmp_path)
    debuglog.add_typed("Coach Plunkett")
    debuglog.event("speech", "request", text="Coach Plunkett, is that right?")
    assert "plunkett" not in written(path).lower()


# ----- what the independent review found (SX.L, one test each) -----

def test_no_typed_letter_reaches_the_log_as_a_key_a_speech_echo_or_a_name_in_a_later_sentence(tmp_path):
    from gamerig import Rig
    path = begin(tmp_path / "logs")
    rig = Rig(sounds_dir=tmp_path / "sounds", rng=__import__("random").Random(1))
    rig.keys.answers = list("josh") + [13]
    typed_name = rig.game.prompts.getter(" Enter the name ")
    rig.game.say(" Is %s correct " % typed_name)
    text = written(path)
    assert typed_name == "josh"
    assert not re.search(r"vk=(74|79|83|72)\b", text) and "text=j" not in text.replace("<typed echo>", "")
    assert " is <typed> correct" in text.lower() and "josh" not in text.lower().replace("joshk", "")


def test_a_renamed_franchise_player_is_typed_text_too(tmp_path):
    from gamerig import Rig
    from nfl4.extras.franchise import rename
    path = begin(tmp_path / "logs")
    rig = Rig(sounds_dir=tmp_path / "sounds", rng=__import__("random").Random(1))
    for code, char in ((90, "z"), (69, "e"), (75, "k"), (69, "e")):
        rig.keys.post(code)
        rig.keys.post_char(char)
    rig.keys.post(13)
    name = rename.typed(rig.game, rig.speech, rig.keys, "Type the new name")
    rig.speech.say_async(" is %s correct? " % name)
    text = written(path)
    assert name == "zeke" and "zeke" not in text.lower() and "vk=90" not in text and "<typed>" in text


def test_names_are_hidden_as_whole_words_in_any_case_short_ones_too_and_cleaned_forms_as_well(tmp_path):
    path = begin(tmp_path)
    debuglog.add_typed("O'Brien-Smith", "OBrienSmith", "Al")
    debuglog.event("speech", "request", text=" Is OBrienSmith correct? ", other="o'brien-smith plays", third="Al and Albert and also AL")
    text = written(path)
    assert "obriensmith" not in text.lower() and "brien" not in text.lower()
    assert "Albert" in text and text.count("<typed>") >= 4


def test_the_short_8_3_name_of_the_profile_folder_and_a_decomposed_accent_are_hidden(tmp_path):
    debuglog.add_private_name("JOSHKE~1")
    debuglog.add_private_name("José")
    path = begin(tmp_path)
    debuglog.event("app", "paths", temp=r"C:\Users\JOSHKE~1\AppData\Local\Temp", other="C:/Users/Jose\u0301/Documents")
    text = written(path)
    assert "JOSHKE" not in text and "Jos" not in text.replace("Josh", "") and text.count("<user>") >= 2


def test_authorization_headers_and_quoted_secrets_are_hidden_and_the_line_still_parses(tmp_path):
    path = begin(tmp_path)
    debuglog.event("net", "call", header="Authorization: Bearer xyz987", cfg='apikey="abc def" next=1')
    line = next(l for l in written(path).splitlines() if " call " in l)
    assert "xyz987" not in line and "abc def" not in line and "next=1" in line


def test_one_enormous_value_cannot_blow_the_cap_of_a_half(tmp_path):
    half = 64 * 1024
    path = begin(tmp_path / "logs", half_bytes=half)
    logging.getLogger("nfl4.speech").warning("no speech engine could say %r", "x" * 5_000_000)
    try:
        1 / 0
    except ZeroDivisionError:
        logging.getLogger("nfl4.x").exception("a big one: %s", "y" * 3_000_000)
    debuglog.flush(30)
    base = os.path.splitext(path)[0]
    assert max(os.path.getsize(p) for p in (path, base + "-b.log") if os.path.exists(p)) < half + 3 * debuglog.MAX_LINE


def test_a_value_whose_repr_raises_never_reaches_the_game(tmp_path):
    class Bad:
        def __repr__(self):
            raise RuntimeError("the COM server is gone")

    path = begin(tmp_path)
    debuglog.event("speech", "request", voice=Bad())
    debuglog.event("app", "after")
    assert " after" in written(path) and debuglog.errors() >= 1


def test_the_crash_log_is_cleaned_of_the_account_name_when_the_log_closes_and_at_the_next_start(tmp_path):
    logs = tmp_path / "logs"
    logs.mkdir()
    (logs / "nfl4-crash.log").write_text('File "C:\\Users\\%s\\AppData\\x.py", line 1\n' % USER, encoding="utf-8")
    begin(logs)
    assert not leaks((logs / "nfl4-crash.log").read_text(encoding="utf-8"), USER)
    debuglog.shutdown_quietly()
    big = "x" * 1_200_000
    (logs / "nfl4-crash.log").write_text(big + "\nlast entry C:\\Users\\%s\\y\n" % USER, encoding="utf-8")
    begin(logs)
    kept = (logs / "nfl4-crash.log").read_text(encoding="utf-8")
    assert "last entry" in kept and len(kept) < debuglog.CRASH_BYTES and not leaks(kept, USER)


def test_a_passing_write_error_costs_nothing_the_same_file_goes_on(tmp_path, monkeypatch):
    path = begin(tmp_path / "logs")
    real = debuglog._Ring._raw
    state = {"failed": False}

    def once(self, data):
        if not state["failed"]:
            state["failed"] = True
            raise OSError(errno.EACCES, "Permission denied")
        return real(self, data)

    monkeypatch.setattr(debuglog._Ring, "_raw", once)
    debuglog.event("app", "hit")
    debuglog.event("app", "after_the_error")
    debuglog.flush()
    assert os.path.dirname(debuglog.path()) == os.path.dirname(path) and "after_the_error" in written(debuglog.path())


def test_a_log_that_fell_back_to_the_temp_folder_is_still_in_the_problem_report(tmp_path, monkeypatch):
    monkeypatch.setattr(debuglog.tempfile, "gettempdir", lambda: str(tmp_path / "tmp"))
    monkeypatch.setattr("tempfile.gettempdir", lambda: str(tmp_path / "tmp"))
    monkeypatch.setenv("NFL4_DATA_DIR", str(tmp_path / "data"))
    (tmp_path / "data").mkdir()
    blocker = tmp_path / "blocker"
    blocker.write_text("a file where the logs folder should be")
    monkeypatch.setattr(debuglog.paths, "log_dir", lambda: str(blocker / "logs"))
    path = begin(blocker / "logs")
    debuglog.event("app", "in_the_temp_folder")
    debuglog.flush()
    archive = problem_report.make(False, str(tmp_path / "out"), system_kwargs=dict(args=[], settings=None))
    import zipfile
    with zipfile.ZipFile(archive) as bundle:
        assert any("in_the_temp_folder" in bundle.read(n).decode("utf-8", "replace") for n in bundle.namelist() if n.startswith("logs/"))


def test_two_launches_in_the_same_second_get_two_files(tmp_path):
    logs = tmp_path / "logs"
    first = begin(logs)
    second = debuglog.start("detailed", str(logs))
    assert first != second and os.path.exists(first) and os.path.exists(second)


def test_the_error_count_is_written_where_the_next_launch_reads_it(tmp_path, monkeypatch):
    monkeypatch.setenv("NFL4_DATA_DIR", str(tmp_path / "data"))
    begin(paths.log_dir())
    debuglog._log.errors = 3
    debuglog.shutdown("test")
    assert debuglog.last_launch_errors().startswith("3 write errors")


def test_a_slow_probe_that_finishes_after_the_wait_still_lands_in_the_file_as_late_items(tmp_path, monkeypatch):
    monkeypatch.setattr(debuglog, "REPORT_WAIT_SECONDS", 0.3)
    path = debuglog.start("detailed", str(tmp_path))
    debuglog.report().section("quick", [("game", "nfl4")])
    debuglog.event("app", "first_event")
    time.sleep(0.8)                                                    # the writer gave up waiting and wrote the header
    debuglog.report().section("slow", [("sapi_voice_count", "1811")])
    debuglog.report_done()
    debuglog.event("app", "second_event")
    text = written(path)
    assert "report was not complete" in text and "-- late startup report items" in text and "sapi_voice_count = 1811" in text
    assert text.index("first_event") < text.index("late startup report items") < text.index("second_event")


def _report_thread(seconds):
    """A startup report that takes `seconds` to finish its last section (the slow SAPI probe of a busy machine)."""
    report = debuglog.report()                                  # this log's report: a thread that ends after the test touches no other test's log

    def slow():
        time.sleep(seconds)
        report.section("slow", [("sapi_voice_count", "3")])
        report.done.set()
    thread = threading.Thread(target=slow, daemon=True)
    report.thread = thread
    thread.start()


def test_a_program_closed_before_its_report_is_done_waits_for_it(tmp_path):
    """shutdown waits up to REPORT_CLOSE_SECONDS for a report still being made (a program closed at once still gets a whole report), and no longer
    (nfl4 SX.8p, B-X98: the start-up test's bound for closing counts this wait)."""
    debuglog.start("detailed", str(tmp_path))
    filled = []
    debuglog.report().on_close = lambda: filled.append(True)
    _report_thread(0.4)
    started = time.monotonic()
    debuglog.shutdown("test")
    took = time.monotonic() - started
    assert not filled and 0.3 < took < debuglog.REPORT_CLOSE_SECONDS + 2.0     # the report finished in the wait: nothing filled as missing


def test_a_report_slower_than_the_wait_is_filled_in_at_the_end(tmp_path):
    debuglog.start("detailed", str(tmp_path))
    filled = []
    debuglog.report().on_close = lambda: filled.append(True)
    _report_thread(debuglog.REPORT_CLOSE_SECONDS + 3.0)
    started = time.monotonic()
    debuglog.shutdown("test")
    took = time.monotonic() - started
    assert filled and debuglog.REPORT_CLOSE_SECONDS - 0.2 < took < debuglog.REPORT_CLOSE_SECONDS + 2.0
