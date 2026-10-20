"""The start-up on the virtual-clock rig: sounds, the title, the first start, the season set-up. This is inspired by Jim Kitchen.

GAME_SPEC 3 steps 3 to 7 (CODE (lifted) Form_Load p_486990 0x486f9b to 0x4882de), rule 0.5.1 (the title), G-F1, G-S8, D-022
item 4, D-006. Every expected list below was written from the lifted lines (the addresses are in game/program.py).
"""
from nfl4.game import extra_texts as words
from nfl4.game import help_texts as H
from nfl4.game import program_texts as P
from nfl4.game import prompt_texts as T
from nfl4.game import texts
from nfl4.speech.roles import ANNOUNCER
from nfl4.speech.voices import VoiceInfo
from programrig import DOWN, ENTER, ESC, preset_season, program_rig, said, sound_events
from seasonrig import RecordingStore

EXIT_KEYS = [DOWN, DOWN, DOWN, ENTER]         # the main menu: choice 4, exit game
INTRO, CROWD1, CROWD2 = "snd_foot0", "snd_foot1", "snd_foot2"
SLOT_ONESHOT, SLOT_CROWD1, SLOT_CROWD2 = 0, 1, 2
WEEK_1 = " This is week  1 of Josh Kennedy's N. F. L. football "      # Str$(1) is " 1": two spaces, as in the original


class Catalog:
    def __init__(self, voices):
        self.list = voices

    def voices(self, timeout=None):
        return list(self.list)


VOICES = [VoiceInfo(0, "id0", "Alpha", "EngA"), VoiceInfo(1, "id1", "Beta", "EngA")]


def marker(rig, text):
    """A note in the speech engine's event list, to see where in the speech a sound call happened."""
    rig.sapi.events.append(("marker", text))


# ----- the sounds of the start-up (0x4876f0 to 0x487b65) -----

def test_the_crowd_beds_start_first_then_the_intro_plays_once_and_loops(tmp_path):
    rig = program_rig(tmp_path, EXIT_KEYS, preset=preset_season()).run()
    plays = [(e.slot, e.sound_id, e.volume, e.loop) for e in rig.slot_log if e.action == "play"][:4]
    assert plays == [(SLOT_CROWD1, CROWD1, -1200, True), (SLOT_CROWD2, CROWD2, -1200, True),
                     (SLOT_ONESHOT, INTRO, 0, False), (SLOT_ONESHOT, INTRO, 0, True)]
    length = [e.time for e in rig.slot_log if e.action == "stop" and e.slot == SLOT_ONESHOT][0] - rig.slot_log[0].time
    assert 1.0 < length < 20.0                               # the intro was waited to its end before it looped


def test_hike_and_play_noise_are_made_after_the_intro_and_play_nothing(tmp_path):
    rig = program_rig(tmp_path, EXIT_KEYS, preset=preset_season()).run()
    volumes = [(e.slot, e.volume) for e in rig.slot_log if e.action == "volume"]
    assert volumes[:2] == [(3, -1600), (6, -2750)]           # MakeHike 0x487b14, MakePlayNoise 0x487b2f
    assert (3, "snd_foot3") not in sound_events(rig) and (6, "snd_foot14") not in sound_events(rig)


def test_the_player_s_sound_volume_is_added_to_every_start_up_level(tmp_path):
    rig = program_rig(tmp_path, EXIT_KEYS, preset=preset_season(), sound_level=-700).run()
    plays = [(e.slot, e.volume) for e in rig.slot_log if e.action == "play"][:3]
    assert plays == [(SLOT_CROWD1, -1900), (SLOT_CROWD2, -1900), (SLOT_ONESHOT, -700)]
    volumes = [(e.slot, e.volume) for e in rig.slot_log if e.action == "volume"]
    assert volumes[:2] == [(3, -2300), (6, -3450)]


# ----- the title (rule 0.5.1, G-F1) -----

def test_a_normal_start_says_the_title_once_stops_the_intro_with_it_then_the_week_line(tmp_path):
    rig = program_rig(tmp_path, EXIT_KEYS, preset=preset_season())
    stops = []
    real = rig.sounds.stop_oneshot
    rig.sounds.stop_oneshot = lambda: (marker(rig, "intro stopped"), stops.append(1), real())[-1]
    rig.run()
    events = [(kind, text) for kind, text in rig.sapi.events if kind in ("speak", "marker")]
    texts_in_order = [text for kind, text in events]
    assert texts_in_order[:4] == [texts.TITLE_SPOKEN, "intro stopped", WEEK_1, " "]       # S8.2 (CLAUDE.md 0.21): the intro ends with the welcome
    assert said(rig).count(texts.TITLE_SPOKEN) == 1 and len(stops) == 1
    assert rig.said[0][1] == ANNOUNCER


def test_notices_follow_the_title_once_each_and_a_broken_source_is_only_logged(tmp_path, caplog):
    class Notices:
        def __init__(self):
            self.pending = ["1 problem found in settings.txt, details are in the log."]

        def take_notices(self):
            taken, self.pending = self.pending, []
            return taken

    class Broken:
        def take_notices(self):
            raise RuntimeError("settings file gone")

    rig = program_rig(tmp_path, EXIT_KEYS, preset=preset_season(), notice_sources=(Notices(), Broken()))
    rig.run()
    assert said(rig)[:3] == [texts.TITLE_SPOKEN, "1 problem found in settings.txt, details are in the log.", WEEK_1]
    assert any("notices of Broken failed" in r.message for r in caplog.records)


def test_with_nvda_the_title_goes_to_nvda_without_a_speaker(tmp_path):
    rig = program_rig(tmp_path, EXIT_KEYS, preset=preset_season(), mode="nvda", nvda_running=True).run()
    assert rig.nvda.said[0] == (texts.TITLE_SPOKEN, None, 0) and rig.said == []


# ----- the first start (0x487bff to 0x487e0d) -----

def first_start_rig(tmp_path, answers, mode="sapi", **kwargs):
    rig = program_rig(tmp_path, answers, first=True, preset=preset_season(), mode=mode, **kwargs)
    rig.game.pause_log = []
    return rig


def test_the_first_start_welcomes_says_the_title_the_key_list_and_where_f9_is(tmp_path):
    rig = first_start_rig(tmp_path, EXIT_KEYS)
    real = rig.sounds.stop_oneshot
    rig.sounds.stop_oneshot = lambda: (marker(rig, "intro stopped"), real())[-1]
    rig.run()
    events = [(kind, text) for kind, text in rig.sapi.events if kind in ("speak", "marker")]
    assert [text for _, text in events][:5] == ["intro stopped", " ", texts.TITLE_SPOKEN, H.SPECIAL_KEYS, words.KEYS_ADDED_F9]
    # the pauses of 0x487d81 and 0x487dea, 0.2 s each, around the key list
    assert [(site, seconds) for site, seconds in rig.game.pause_log if site in (0x487d81, 0x487dea)] == [
        (0x487d81, 0.2), (0x487dea, 0.2)]
    assert said(rig).count(texts.TITLE_SPOKEN) == 1                    # no second welcome at the first start
    assert P.WELCOME_TO not in said(rig)                               # the original's " Welcome to " is part of the sentence (rule 0.16)


def test_the_first_start_waits_for_the_welcome_to_end_before_the_title(tmp_path):
    # the intro stops, Voice.Speak " ", 0 (0x487cfa), then say (waited) the welcome sentence, which replaces the original's
    # say2 " Welcome to " and its title (rule 0.16)
    rig = first_start_rig(tmp_path, EXIT_KEYS, speech_per_char=0.01)
    real = rig.sounds.stop_oneshot
    rig.sounds.stop_oneshot = lambda: (marker(rig, "intro stopped"), real())[-1]
    rig.run()
    kinds = [(kind, text[:13]) for kind, text in rig.sapi.events][:8]
    assert kinds == [("marker", "intro stopped"), ("speak", " "), ("wait", ""), ("speak", "Welcome to Jo"), ("wait", ""),
                     ("stop", ""), ("speak", "Special key i"), ("speak", " F9. added fu")]


def test_the_first_start_asks_the_five_voices_when_sapi_speaks(tmp_path):
    rig = first_start_rig(tmp_path, [ESC] * 5 + EXIT_KEYS)
    rig.game.options.voice_catalog = Catalog(VOICES)
    rig.run()
    titles = [text.split(".")[0] for text in said(rig) if text.startswith("Choose the voice for")]
    assert titles == ["Choose the voice for the announcer", "Choose the voice for your quarterback",
                      "Choose the voice for your opponents quarterback", "Choose the voice for your punter",
                      "Choose the voice for your opponents punter"]
    # the choice comes after the key list and its F9 sentence, before the week line
    spoken = said(rig)
    assert spoken.index(H.SPECIAL_KEYS) < spoken.index(words.KEYS_ADDED_F9) < spoken.index(
        next(t for t in spoken if t.startswith("Choose the voice for"))) < spoken.index(WEEK_1)


def test_the_first_start_asks_no_voices_when_a_screen_reader_speaks_d022(tmp_path):
    rig = first_start_rig(tmp_path, EXIT_KEYS, mode="nvda", nvda_running=True)
    rig.game.options.voice_catalog = Catalog(VOICES)
    rig.run()
    spoken = rig.nvda.spoken()
    assert [t for t in spoken if t.startswith("Choose the voice")] == []
    assert spoken[:4] == [" ", texts.TITLE_SPOKEN, H.SPECIAL_KEYS, words.KEYS_ADDED_F9]


def test_a_later_start_has_no_welcome_no_key_list_and_no_voice_choice(tmp_path):
    rig = program_rig(tmp_path, EXIT_KEYS, preset=preset_season())
    rig.game.options.voice_catalog = Catalog(VOICES)
    rig.run()
    spoken = said(rig)
    assert P.WELCOME_TO not in spoken and H.SPECIAL_KEYS not in spoken and words.KEYS_ADDED_F9 not in spoken
    assert [t for t in spoken if t.startswith("Choose the voice")] == []


# ----- the season set-up (0x488018 to 0x4882de) -----

def test_a_new_season_asks_the_coach_the_team_makes_the_schedule_and_writes_week_1(tmp_path):
    answers = ["k", "i", "m", ENTER, ENTER,          # the coach, "kim", yes
               ENTER, ENTER] + EXIT_KEYS             # the first team (Bengals), yes; then the main menu: exit
    rig = program_rig(tmp_path, answers)
    rig.game.season_store = RecordingStore()
    stores = []
    rig.game.setup_store = type("S", (), {
        "write_coach_and_team": lambda self, a, b, c: stores.append(("team", a, b, c)),
        "write_schedule": lambda self, schedule: stores.append(("schedule", len(schedule))),
        "append_quarterback": lambda self, name: stores.append(("quarterback", name))})()
    rig.run()
    assert stores == [("team", 1, 1, "kim"), ("schedule", 16)]
    assert rig.game.season_store.events == [("gtp", 1)]
    spoken = said(rig)
    assert spoken[1:2] == [T.ENTER_COACH]                                # after the title: the coach prompt
    assert spoken.index(" kim choose your team ") < spoken.index(WEEK_1)
    assert rig.store.calls[0] == "load_season" and rig.game.season.gtp == 1 and rig.game.season.coach == "kim"


def test_a_season_that_continues_asks_nothing_and_goes_to_the_week_line(tmp_path):
    rig = program_rig(tmp_path, EXIT_KEYS, preset=preset_season(coach="Bob", team=(3, 2), gtp=5)).run()
    spoken = said(rig)
    assert T.ENTER_COACH not in spoken and spoken[1] == " This is week  5 of Josh Kennedy's N. F. L. football "


def test_the_log_is_opened_once_after_the_season_is_read_and_starts_with_the_title_line(tmp_path):
    rig = program_rig(tmp_path, EXIT_KEYS, preset=preset_season())
    lines = []
    rig.game.log_sink = lines.append
    rig.run()
    assert rig.store.calls[:2] == ["load_season", ("open_log", True)]            # 0x48836a: no saved game and week 1: Output
    today = " Today's game is Bengals 0 and  0 verses the %s 0 and  0" % rig.game.opponent_team()
    assert lines == [texts.CAPTION, "",                                          # 0x488422, 0x48842f
                     " This is week #1 of Josh Kennedy's N. F. L. football ",             # 0x4885c8 Print #3 (Trim$ number)
                     "", today, ""]                                              # 0x48981b, 0x48982b, 0x489845


def test_the_log_is_appended_to_in_a_later_week_or_with_a_saved_game(tmp_path):
    rig = program_rig(tmp_path, EXIT_KEYS, preset=preset_season(gtp=4))
    lines = []
    rig.game.log_sink = lines.append
    rig.run()
    assert rig.store.calls[:2] == ["load_season", ("open_log", False)] and lines[0] == ""
