"""The whole program through app.main(): the title, no voice, a window closed while the game talks, the crash guard
for the five speakers' voices. This is inspired by Jim Kitchen.

The real Win32 window and the real game thread run; speech is a fake so nothing is heard. The window shows for about a
second each time. The player's folders are not touched (NFL4_DATA_DIR in tmp_path). Rule 0.5.1, CLAUDE.md 0.10,
GAP_REGISTER G-F1, G-F8, G-F9, playbook 7.2.1 and 7.4.5.
"""
import os
import threading
import time

import pytest

import nfl4.app as app
from nfl4.game import extra_texts
import nfl4.audio.engine as audio_engine
import nfl4.ui.window as window_module
from nfl4.audio.engine import NO_SOUND_NOTICE
from nfl4.audio.library import SOUND_FILE_NOTICE
from nfl4.audio.output import OutputError
from nfl4.data import debuglog
from nfl4.data.voiceguard import CRASHED_FILE, TRIAL_FILE
from nfl4.game import program_texts, texts
from nfl4.speech.fake import FakeBackend
from nfl4.speech.manager import SpeechManager
from nfl4.speech.roles import ANNOUNCER, OPPONENT_PUNTER, OWN_QUARTERBACK
from nfl4.speech.sapi5 import SapiStart
from wavmaker import sine, write

SMOOTH = r"HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech\Voices\TokenEnums\SmoothTalker\SmoothTalker"


@pytest.fixture(autouse=True)
def sound_on_the_dummy_driver(monkeypatch):
    """The program starts the mixer (S7.2); here on SDL's silent dummy driver, so no test depends on a sound device."""
    monkeypatch.setenv("SDL_AUDIODRIVER", "dummy")


@pytest.fixture(autouse=True)
def window_stays_in_the_background(monkeypatch):
    """The program's show() brings its window to the front and takes the keyboard; in a test that would interrupt the
    owner's screen reader every run (and a key of the owner could land in it, B-X14). The window exists and gets the
    posted messages either way."""
    monkeypatch.setattr(window_module.GameWindow, "show", lambda self: False)


@pytest.fixture(autouse=True)
def not_the_first_start(tmp_path):
    """A settings.txt that is already there makes the start an ordinary one: no welcome, no key list, no voice choice (S7.4b).
    The tests that want the first start delete it. A short foot0.wav of the player's stands in for the 3.4 s intro jingle,
    which the program plays to its end before it says the title (G-F1): the windows here close after a second."""
    write_settings(tmp_path, [])
    (tmp_path / "sounds").mkdir(exist_ok=True)
    write(tmp_path / "sounds" / "foot0.wav", sine(400, 0.05, 11025), rate=11025)


class Made:
    """A fake create_speech: records what main() asked for and hands back fakes."""

    def __init__(self, ok=True, nvda=None, per_char=0.0):
        self.sapi = FakeBackend(name="SAPI 5", takes_roles=True, seconds_per_char=per_char)
        self.manager = SpeechManager(self.sapi, nvda, "sapi")
        self.started = SapiStart(ok=ok, voice_count=3 if ok else 0, voice_id="first", voice_name="First voice",
                                 error="" if ok else "no SAPI 5 voices installed")
        self.calls = []

    def __call__(self, speech_settings, skip=frozenset(), arm=None, clear=None):
        self.calls.append((dict(speech_settings.voices), skip, arm, clear))
        for role, voice in speech_settings.voices.items():       # the voices SAPI would resolve
            if voice and voice.strip().lower() not in skip:
                self.sapi.role_voices[role] = voice
        return self.manager, self.started


def closing_after(seconds):
    real = window_module.GameWindow

    class Closing(real):
        """The player closes the window `seconds` after it opens."""

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.closed_at = []
            threading.Timer(seconds, self.close_now).start()

        def close_now(self):
            Closing.closed.append(time.monotonic())
            self.close()

    Closing.closed = []
    return Closing


def launch_log(folder) -> str:
    """The text of the newest launch log in the logs folder (playbook 7.11: one file per launch; both halves)."""
    debuglog.flush(debuglog.REPORT_WAIT_SECONDS + 10)          # the writer holds the first lines for the startup report: wait past the hold (B-X97)
    logs = sorted(p for p in (folder / "logs").glob("nfl4-2*.log"))
    assert logs, "no launch log was written"
    return "\n".join(p.read_text(encoding="utf-8") for p in logs[-2:])


def write_settings(folder, lines):
    (folder / "settings.txt").write_text("# NFL Football 4 settings, format 1\n" + "".join(l + "\n" for l in lines),
                                         encoding="utf-8")


@pytest.mark.window
def test_a_normal_start_says_the_title_and_closes_cleanly(tmp_path, monkeypatch):
    monkeypatch.setenv("NFL4_DATA_DIR", str(tmp_path))
    made = Made()
    monkeypatch.setattr(app, "create_speech", made)
    window = closing_after(1.0)
    monkeypatch.setattr(window_module, "GameWindow", window)
    assert app.main() == 0
    assert made.sapi.said[0] == (texts.TITLE_SPOKEN, ANNOUNCER, 0)
    # S7.1's 2.5 s to close, plus the wait for a startup report still running (SX.L): under a whole suite the report's speech section took
    # 4.4 s and the close 2.6 s (nfl4 SX.8p, B-X98)
    assert window.closed and time.monotonic() - window.closed[0] < 2.5 + debuglog.REPORT_CLOSE_SECONDS
    assert (tmp_path / "settings.txt").is_file() and not (tmp_path / TRIAL_FILE).exists()
    log_text = launch_log(tmp_path)
    assert "NFL Football 4 closed" in log_text
    assert os.path.normcase(os.getcwd()) == os.path.normcase(str(tmp_path))  # left the program folder (7.2.1)


def test_the_welcome_sentence_is_exactly_the_owners_and_the_caption_is_unchanged():
    """Rule 0.16, playbook 7.12: both parts, the letters of NFL spaced for the voices, no second welcome; rule 0.5.1 keeps the caption."""
    assert texts.TITLE_SPOKEN == "Welcome to Josh Kennedy's N. F. L. football, loosely inspired by Jim Kitchen's original games."
    assert texts.GAME_SPOKEN == "N. F. L. football" and texts.INSPIRATION == "Jim Kitchen's original games"
    assert texts.TITLE_SPOKEN.lower().count("welcome") == 1 and "NFL" not in texts.TITLE_SPOKEN
    assert texts.CAPTION == "NFL Football 4 by Josh Kennedy, inspired by Jim Kitchen"


@pytest.mark.window
def test_the_welcome_is_spoken_once_per_launch_where_the_title_was_and_the_log_says_so(tmp_path, monkeypatch):
    monkeypatch.setenv("NFL4_DATA_DIR", str(tmp_path))
    made = Made()
    monkeypatch.setattr(app, "create_speech", made)
    monkeypatch.setattr(window_module, "GameWindow", closing_after(1.0))
    assert app.main() == 0
    assert made.sapi.spoken()[0] == texts.TITLE_SPOKEN and made.sapi.spoken().count(texts.TITLE_SPOKEN) == 1
    log_text = launch_log(tmp_path)
    assert log_text.count(" welcome_spoken ") == 1 and "welcome_sentence = " + texts.TITLE_SPOKEN in log_text


@pytest.mark.window
def test_a_real_start_writes_a_complete_startup_report_and_the_events_after_it(tmp_path, monkeypatch):
    monkeypatch.setenv("NFL4_DATA_DIR", str(tmp_path))
    monkeypatch.setattr(app, "create_speech", Made())
    monkeypatch.setattr(window_module, "GameWindow", closing_after(1.0))
    assert app.main() == 0
    lines = launch_log(tmp_path).splitlines()
    assert lines[0].startswith("==== startup report") and "==== end of startup report ====" in lines
    held = {l.split(" = ", 1)[0]: l.split(" = ", 1)[1] for l in lines[:lines.index("==== end of startup report ====")] if " = " in l}
    from nfl4.data.sysreport import REQUIRED_KEYS
    assert [k for k in REQUIRED_KEYS if not held.get(k, "").strip()] == []
    assert all(v.startswith("n/a (") for v in held.values() if v.startswith("n/a"))
    after = lines[lines.index("==== end of startup report ====") + 1:]
    assert any(" key " in l or " speech " in l for l in after) and any(" window_close" in l for l in after)


@pytest.mark.window
def test_the_start_that_makes_settings_txt_is_the_first_start_with_the_welcome(tmp_path, monkeypatch):
    """The original's missing footbal0.dat (GAME_SPEC 3 step 6): the welcome sentence (rule 0.16), the key list and where F9 is."""
    monkeypatch.setenv("NFL4_DATA_DIR", str(tmp_path))
    (tmp_path / "settings.txt").unlink()
    made = Made()
    monkeypatch.setattr(app, "create_speech", made)
    monkeypatch.setattr(window_module, "GameWindow", closing_after(1.5))
    assert app.main() == 0
    spoken = made.sapi.spoken()
    assert spoken[:2] == [" ", texts.TITLE_SPOKEN] and program_texts.WELCOME_TO not in spoken     # the sentence says "Welcome to" itself
    assert extra_texts.KEYS_ADDED_F9 in spoken and (tmp_path / "settings.txt").is_file()


@pytest.mark.window
def test_a_sound_file_that_cannot_be_used_is_reported_once_at_start(tmp_path, monkeypatch):
    """G-A6: every sound is resolved at start, so the notice comes with the start-up notices, once."""
    monkeypatch.setenv("NFL4_DATA_DIR", str(tmp_path))
    (tmp_path / "sounds").mkdir(exist_ok=True)
    (tmp_path / "sounds" / "foot7.wav").write_bytes(b"RIFF this is not a sound")
    (tmp_path / "sounds" / "foot12.wav").write_bytes(b"")
    made = Made()
    monkeypatch.setattr(app, "create_speech", made)
    monkeypatch.setattr(window_module, "GameWindow", closing_after(1.0))
    assert app.main() == 0
    spoken = made.sapi.spoken()
    assert spoken[0] == texts.TITLE_SPOKEN and spoken.count(SOUND_FILE_NOTICE) == 1
    assert (tmp_path / "sounds" / "sounds.txt").is_file()
    log_text = launch_log(tmp_path)
    assert "foot7.wav cannot be used" in log_text and "foot12.wav cannot be used" in log_text


@pytest.mark.window
def test_no_sound_device_is_said_once_and_the_program_runs_on(tmp_path, monkeypatch):
    """G-A4: the game goes on without sound and says so once."""
    monkeypatch.setenv("NFL4_DATA_DIR", str(tmp_path))

    def no_device(*args, **kwargs):
        raise OutputError("no sound device")
    monkeypatch.setattr(audio_engine, "PygameOutput", no_device)
    made = Made()
    monkeypatch.setattr(app, "create_speech", made)
    monkeypatch.setattr(window_module, "GameWindow", closing_after(1.0))
    assert app.main() == 0
    assert made.sapi.spoken().count(NO_SOUND_NOTICE) == 1


@pytest.mark.window
def test_no_sapi_voice_shows_the_box_tells_nvda_and_exits_cleanly(tmp_path, monkeypatch):
    monkeypatch.setenv("NFL4_DATA_DIR", str(tmp_path))
    nvda = FakeBackend(name="NVDA")
    made = Made(ok=False, nvda=nvda)
    monkeypatch.setattr(app, "create_speech", made)
    boxes = []
    monkeypatch.setattr(window_module.GameWindow, "message_box", lambda self, text, title: boxes.append((text, title)))
    assert app.main() == 1                                                    # G-F9: the box, then a clean exit
    assert nvda.spoken() == [texts.NO_VOICES_SPOKEN]                          # the screen reader hears the same words
    assert boxes == [(texts.NO_VOICES + "\n" + texts.NO_VOICES_CONTACT, texts.MESSAGE_TITLE)]
    assert "Jim Kitchen" not in boxes[0][0] and "github.com/joshknnd1982" in boxes[0][0]   # D-008: no contact details
    assert made.sapi.said == []


@pytest.mark.window
def test_closing_the_window_while_the_game_talks_ends_the_program_within_two_seconds(tmp_path, monkeypatch):
    monkeypatch.setenv("NFL4_DATA_DIR", str(tmp_path))
    made = Made(per_char=0.2)                                                 # the title alone would take 11 seconds
    monkeypatch.setattr(app, "create_speech", made)
    window = closing_after(1.0)
    monkeypatch.setattr(window_module, "GameWindow", window)
    assert app.main() == 0
    assert window.closed and time.monotonic() - window.closed[0] < 2.5 + debuglog.REPORT_CLOSE_SECONDS     # and the report's wait (SX.L, B-X98)
    assert made.sapi.spoken()[0] == texts.TITLE_SPOKEN                       # it really was in the middle of the title


@pytest.mark.window
def test_after_a_crash_the_speakers_with_that_voice_use_the_first_voice_and_the_game_says_so(tmp_path, monkeypatch):
    monkeypatch.setenv("NFL4_DATA_DIR", str(tmp_path))
    write_settings(tmp_path, [f"voice_own_quarterback = {SMOOTH}", f"voice_opponent_punter = {SMOOTH}",
                              "voice_announcer = token-7"])
    (tmp_path / TRIAL_FILE).write_text(SMOOTH + "\n")              # the last run died while this voice was in trial
    made = Made()
    made.sapi.role_voices[ANNOUNCER] = "token-7"
    monkeypatch.setattr(app, "create_speech", made)
    monkeypatch.setattr(window_module, "GameWindow", closing_after(1.0))
    assert app.main() == 0
    voices, skip, arm, clear = made.calls[0]
    assert skip == frozenset({SMOOTH.lower()})                     # not opened for either speaker
    spoken = made.sapi.spoken()
    crashed = [t for t in spoken if "The voice SmoothTalker crashed NFL Football 4 last time" in t]
    assert len(crashed) == 1 and "F12" in crashed[0]               # one notice for the voice, not one per speaker
    assert spoken.index(crashed[0]) > spoken.index(texts.TITLE_SPOKEN)
    text = (tmp_path / "settings.txt").read_text(encoding="utf-8")
    assert f"voice_own_quarterback = {SMOOTH}" in text and f"voice_opponent_punter = {SMOOTH}" in text  # kept
    assert SMOOTH in (tmp_path / CRASHED_FILE).read_text()
    assert not (tmp_path / TRIAL_FILE).exists()                    # closed normally: no new trial left


@pytest.mark.window
def test_the_guard_hooks_arm_a_new_voice_and_clear_only_that_voice(tmp_path, monkeypatch):
    monkeypatch.setenv("NFL4_DATA_DIR", str(tmp_path))
    made = Made()
    monkeypatch.setattr(app, "create_speech", made)
    trial_seen = []
    real = window_module.GameWindow

    class Probe(real):
        def __init__(self, *a, **k):
            super().__init__(*a, **k)
            threading.Timer(0.8, self.check).start()

        def check(self):
            _, _, arm, clear = made.calls[0]
            arm("")                                                # the first voice is never armed
            trial_seen.append((tmp_path / TRIAL_FILE).exists())
            arm("token-3")
            trial_seen.append((tmp_path / TRIAL_FILE).read_text().strip())
            clear("token-9")                                       # another voice proven: token-3's trial stays
            trial_seen.append((tmp_path / TRIAL_FILE).exists())
            clear("TOKEN-3")
            trial_seen.append((tmp_path / TRIAL_FILE).exists())
            self.close()

    monkeypatch.setattr(window_module, "GameWindow", Probe)
    assert app.main() == 0
    assert trial_seen == [False, "token-3", True, False]


@pytest.mark.window
def test_a_saved_voice_that_is_not_installed_is_told_once(tmp_path, monkeypatch):
    monkeypatch.setenv("NFL4_DATA_DIR", str(tmp_path))
    write_settings(tmp_path, ["voice_own_quarterback = token-gone", "voice_opponent_punter = token-also-gone"])
    made = Made()
    monkeypatch.setattr(app, "create_speech", made)

    def resolve_to_first(role, timeout=3.0):
        from nfl4.speech.sapi5 import VoiceDetails
        return VoiceDetails("first", "First voice", "")

    made.sapi.role_details = resolve_to_first
    monkeypatch.setattr(window_module, "GameWindow", closing_after(1.0))
    assert app.main() == 0
    spoken = made.sapi.spoken()
    assert spoken.count("A voice saved in the settings was not found, so the first voice is used for it.") == 1


# ----- the player's files (S7.5, data/files/store.py) -----

def a_season_in(folder, gtp=5):
    """What the program writes by week `gtp`: the files of the first game of week 1 and a records file after it."""
    import random

    from nfl4.data.files.store import FileProgramStore
    from nfl4.game.rnd import GameRandom
    from nfl4.game.schedule import make_schedule
    from nfl4.game.standings import Records
    store = FileProgramStore(str(folder), str(folder / "customize"))
    store.write_coach_and_team(3, 2, "Kim Lee")
    store.write_schedule(make_schedule(GameRandom(random.Random(5)), 3, 2))
    store.write_gtp(gtp)
    store.write_records(Records())


@pytest.mark.window
def test_a_season_on_disk_is_announced_by_the_start_up_question_and_nothing_is_started_without_a_key(tmp_path, monkeypatch):
    from nfl4.game import save_texts
    monkeypatch.setenv("NFL4_DATA_DIR", str(tmp_path))
    a_season_in(tmp_path, gtp=5)
    (tmp_path / "footballlog.txt").write_bytes(b"an earlier week\r\n")
    made = Made()
    monkeypatch.setattr(app, "create_speech", made)
    monkeypatch.setattr(window_module, "GameWindow", closing_after(1.5))
    assert app.main() == 0
    spoken = made.sapi.spoken()
    assert spoken[0] == texts.TITLE_SPOKEN                                   # SX.14 (rule 0.23): then the sentence about the season and the question
    assert any(t.startswith(" You have a season in progress") and "week 5" in t for t in spoken) and save_texts.MENU_PROMPT in spoken
    assert not any(t.startswith(" This is week") for t in spoken)           # no key was pressed: the week is not started
    assert (tmp_path / "footballlog.txt").read_bytes() == b"an earlier week\r\n"
    assert not (tmp_path / "customize" / "footplay.txt").exists()          # no game was played: no names of the player's own


@pytest.mark.window
def test_a_damaged_season_is_said_after_the_title_and_a_copy_is_kept(tmp_path, monkeypatch):
    from nfl4.data.files.store import SEASON_DAMAGED
    monkeypatch.setenv("NFL4_DATA_DIR", str(tmp_path))
    a_season_in(tmp_path, gtp=5)
    (tmp_path / "footbal2.dat").write_bytes(b"cut short")
    made = Made()
    monkeypatch.setattr(app, "create_speech", made)
    monkeypatch.setattr(window_module, "GameWindow", closing_after(1.5))
    assert app.main() == 0
    spoken = made.sapi.spoken()
    assert spoken[0] == texts.TITLE_SPOKEN and spoken[1] == SEASON_DAMAGED and spoken.count(SEASON_DAMAGED) == 1
    assert (tmp_path / "footbal2.dat.damaged1").is_file() and not (tmp_path / "footbal2.dat").exists()
    assert not (tmp_path / "footbal1.dat").exists()                       # the new season has not been chosen yet


@pytest.mark.window
def test_a_start_with_no_files_asks_for_the_coach_and_writes_no_season_file_before_the_answers(tmp_path, monkeypatch):
    """With rules = classic the original's start: the coach's name first (SX.9: a new player's default is the N. F. L. rules, below)."""
    from nfl4.game import prompt_texts
    monkeypatch.setenv("NFL4_DATA_DIR", str(tmp_path))
    write_settings(tmp_path, ["rules = classic"])
    made = Made()
    monkeypatch.setattr(app, "create_speech", made)
    monkeypatch.setattr(window_module, "GameWindow", closing_after(1.0))
    assert app.main() == 0
    assert prompt_texts.ENTER_COACH in made.sapi.spoken()
    assert sorted(p.name for p in tmp_path.iterdir() if p.is_file() and p.name.endswith((".dat", ".gtp", ".sav", ".txt"))) \
        == ["settings.txt"]


@pytest.mark.window
def test_a_new_player_starts_with_the_nfl_rules_and_is_asked_the_kind_of_season_first(tmp_path, monkeypatch):
    """SX.9 (NQ2, D-079): no settings file: the N. F. L. rules; the new season's question (classic season first) comes before the coach's name,
    and nothing of a season or a franchise is written before the answers."""
    from nfl4.extras import nx_texts as X
    monkeypatch.setenv("NFL4_DATA_DIR", str(tmp_path))
    made = Made()
    monkeypatch.setattr(app, "create_speech", made)
    monkeypatch.setattr(window_module, "GameWindow", closing_after(1.0))
    assert app.main() == 0
    spoken = made.sapi.spoken()
    assert X.text("NXF-01", coach="coach") in spoken
    assert sorted(p.name for p in tmp_path.iterdir() if p.is_file() and p.name.endswith((".dat", ".gtp", ".sav", ".txt"))) \
        == ["settings.txt"]
    assert not (tmp_path / "franchise").exists()


# ----- the player's names and banter (S7.7, data/customize.py) -----

@pytest.mark.window
def test_a_start_makes_the_customization_files_and_says_nothing_about_them(tmp_path, monkeypatch):
    monkeypatch.setenv("NFL4_DATA_DIR", str(tmp_path))
    write_settings(tmp_path, ["rules = classic"])
    made = Made()
    monkeypatch.setattr(app, "create_speech", made)
    monkeypatch.setattr(window_module, "GameWindow", closing_after(1.0))
    assert app.main() == 0
    # Classic: no file of the extras (remarks.txt) is made (nfl4 only, CUSTOMIZABLE_CONTENT 13, SX.2; the default since SX.9 is the N. F. L. rules)
    assert sorted(p.name for p in (tmp_path / "customize").iterdir()) == ["banter.txt", "divisions.txt", "sounds",
                                                                         "surnames.txt", "teams.txt"]
    spoken = " ".join(made.sapi.spoken())
    assert "teams.txt" not in spoken and "banter.txt" not in spoken and "customiz" not in spoken


@pytest.mark.window
def test_a_start_with_the_nfl_rules_also_makes_remarks_txt_and_says_nothing_about_it(tmp_path, monkeypatch):
    """nfl4 only (rule 0.13, PX SX.2): settings.txt says rules = nfl, so the extras' file is read (made) at the start."""
    monkeypatch.setenv("NFL4_DATA_DIR", str(tmp_path))
    write_settings(tmp_path, ["rules = nfl"])
    made = Made()
    monkeypatch.setattr(app, "create_speech", made)
    monkeypatch.setattr(window_module, "GameWindow", closing_after(1.0))
    assert app.main() == 0
    remarks = tmp_path / "customize" / "remarks.txt"
    assert remarks.is_file() and b"TO01 = " in remarks.read_bytes()
    assert "remarks" not in " ".join(made.sapi.spoken())
    assert "rules = nfl" in (tmp_path / "settings.txt").read_text(encoding="utf-8")


@pytest.mark.window
def test_a_damaged_banter_file_is_said_after_the_title_and_a_copy_is_kept(tmp_path, monkeypatch):
    monkeypatch.setenv("NFL4_DATA_DIR", str(tmp_path))
    (tmp_path / "customize").mkdir()
    junk = b"\x00\x01 not a list"
    (tmp_path / "customize" / "banter.txt").write_bytes(junk)
    made = Made()
    monkeypatch.setattr(app, "create_speech", made)
    monkeypatch.setattr(window_module, "GameWindow", closing_after(1.2))
    assert app.main() == 0
    spoken = made.sapi.spoken()
    notice = " The file banter.txt was damaged and has been reset to the original banter lines. A copy was saved. "
    assert spoken[0] == texts.TITLE_SPOKEN and spoken[1] == notice and spoken.count(notice) == 1
    assert (tmp_path / "customize" / "banter.txt.damaged1").read_bytes() == junk
    assert b"B001 = " in (tmp_path / "customize" / "banter.txt").read_bytes()


@pytest.mark.window
def test_a_renamed_team_is_spoken_in_the_week_and_a_season_on_disk_still_finds_it_by_its_number(tmp_path, monkeypatch):
    monkeypatch.setenv("NFL4_DATA_DIR", str(tmp_path))
    a_season_in(tmp_path, gtp=5)                                          # the player's team is division 3, place 2: T10
    (tmp_path / "customize").mkdir()
    (tmp_path / "customize" / "teams.txt").write_bytes(b"# NFL Football 4 teams, format 1.\r\nT10 = Mustangs\r\n")
    made = Made()
    monkeypatch.setattr(app, "create_speech", made)
    monkeypatch.setattr(window_module, "GameWindow", closing_after(1.5))
    assert app.main() == 0
    spoken = made.sapi.spoken()
    assert any("Mustangs" in line for line in spoken) and not any("Chargers" in line for line in spoken)
    assert not (tmp_path / "customize" / "teams.txt.damaged1").exists()
