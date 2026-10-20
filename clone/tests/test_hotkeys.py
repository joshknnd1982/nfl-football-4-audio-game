"""The key layer and the seven hot-key menus on the virtual-clock rig. This is inspired by Jim Kitchen.

GAME_SPEC 4.1 to 4.8 and 8.1 (CODE (lifted) Form_KeyDown p_42e5e0, speckeys p_420860, readins p_420040, SayHints
p_420b50, ctog p_4216b0, adjrate p_423530, adjvol p_421960, ChangeVoice p_4239c0), D-018 (the F1 hand-back), D-022, D-023,
D-014, G-S8, Q58, Q59; NFL_EXTRAS_DESIGN 3 H12. Every expected list of events below was written from the lifted lines
(the addresses are in game/hotkeys.py): a global key typed at an ordinary wait runs its menu inside the pump and the
wait ends with F1 ("112").
"""
import pytest

from gamerig import Rig
from nfl4.audio.output import SLOT_CROWD1, SLOT_CROWD2, SLOT_HIKE
from nfl4.data.settings import Settings
from nfl4.game import extra_texts as words
from nfl4.game import help_texts as H
from nfl4.game import prompt_texts as T
from nfl4.game.keys import KeyInput
from nfl4.game.options import Options
from nfl4.game.rules import ClassicRules
from nfl4.speech.roles import (ANNOUNCER, F11_NAMES, OPPONENT_PUNTER, OPPONENT_QUARTERBACK, OWN_PUNTER,
                               OWN_QUARTERBACK)
from nfl4.speech.voices import VoiceInfo

F1, F5, F6, F7, F8, F11, F12, CTRL = 112, 116, 117, 118, 119, 122, 123, 17
ENTER, ESC, UP, DOWN, HOME, A_KEY = 13, 27, 38, 40, 36, 65
SPEECH = 0.01                     # seconds per character of the fake speech


def events(rig, kinds=("speak", "stop", "wait")):
    return [(kind, text) for kind, text in rig.sapi.events if kind in kinds]


def run_key(rig):
    """An ordinary wait (getkey) where the test types its answers; returns the key code text it ended with."""
    rig.keys.getkey(rig.speech)
    return rig.keys.code_text


class Saves:
    def __init__(self):
        self.count = 0

    def __call__(self):
        self.count += 1
        return True


def with_options(rig, base_rate=0, **settings_changes):
    settings = Settings.defaults()
    if rig.sounds is not None:
        settings.audio = rig.sounds.settings
    saves = Saves()
    rig.game.options = Options(settings, rig.speech, save=saves, base_rate=lambda: base_rate)
    return rig.game.options, saves


# ----- Form_KeyDown -----

def test_alt_and_f10_are_the_escape_code_with_no_character_and_run_no_menu():
    keys = KeyInput()
    seen = []
    keys.key_handler = seen.append
    for code in (18, 121):
        keys.post(code)
        keys.pump()
        assert (keys.code_text, keys.char) == ("27", "")
    keys.post(A_KEY)
    keys.pump()
    assert (keys.code_text, keys.char) == ("65", "a")
    assert seen == ["65"]                               # the handler sees every other key, inside the pump


def test_a_key_that_is_not_global_runs_no_menu():
    rig = Rig([A_KEY])
    assert run_key(rig) == "65"
    assert rig.game.hotkeys.runs == []


def test_a_global_key_during_a_pause_runs_its_menu_and_the_next_wait_clears_the_f1():
    # dy pumps but never ends on a key (GAME_SPEC 7): F8 runs inside it; the F1 it leaves is cleared by the next clk
    rig = Rig([A_KEY])
    with_options(rig)
    rig.keys.post(F8)
    rig.game.dy(1.0)
    assert rig.game.hotkeys.runs == ["119"] and rig.keys.code_text == "112"
    assert run_key(rig) == "65"


def test_a_global_key_at_the_games_wait_with_ambient_sounds_ends_it_as_f1(tmp_path):
    rig = Rig([F8], sounds_dir=tmp_path)
    rig.keys.getkey2(rig.speech, rig.sounds)
    assert rig.keys.code_text == "112" and rig.game.hotkeys.runs == ["119"]


def test_a_global_key_typed_during_a_waited_line_runs_at_the_next_pump_and_that_wait_ends_as_f1():
    # G-K1: a synchronous line pumps nothing; the key is delivered by the first DoEvents of the next getkey's clk,
    # its menu runs there and leaves "112", so the wait ends at once as if F1 had been pressed (D-018)
    rig = Rig([])
    rig.keys.post(F8)
    rig.game.say(" A line. ")
    assert rig.game.hotkeys.runs == []
    assert run_key(rig) == "112" and rig.game.hotkeys.runs == ["119"]
    assert rig.keys.waits == 1


# ----- F5, speckeys -----

def test_f5_speaks_the_key_list_waits_for_its_end_and_hands_f1_back():
    rig = Rig([F5], speech_per_char=SPEECH)
    start = rig.clock.now
    assert run_key(rig) == "112"
    assert events(rig) == [("stop", ""), ("speak", H.SPECIAL_KEYS), ("speak", words.KEYS_ADDED_F9), ("stop", "")]   # the last stop is getkey's
    assert rig.said[0] == (H.SPECIAL_KEYS, ANNOUNCER, 0)                         # say5: the announcer
    assert rig.clock.now - start == pytest.approx((len(H.SPECIAL_KEYS) + len(words.KEYS_ADDED_F9)) * SPEECH, abs=0.01)
    assert rig.game.hotkeys.runs == ["116"]


def test_the_key_list_is_the_original_text():
    assert H.SPECIAL_KEYS.startswith("Special key instructions. F1. repeat current prompt. F2. instant replay. ")
    assert H.SPECIAL_KEYS.endswith("F12. change voice. Control key, adjust rate of speech. escape key, exit game. ")
    assert len(H.SPECIAL_KEYS_PIECES) == 13 and H.SPECIAL_KEYS_JOINER == ""


def test_a_key_during_the_key_list_stops_it_and_still_hands_f1_back():
    rig = Rig([F5, ("cut", 1.0, A_KEY)], speech_per_char=SPEECH)
    assert run_key(rig) == "112"
    assert events(rig) == [("stop", ""), ("speak", H.SPECIAL_KEYS), ("speak", words.KEYS_ADDED_F9), ("stop", ""), ("stop", "")]


def test_a_global_key_inside_a_menu_nests_a_second_menu():
    # F6 during the F5 text: readins runs to its end inside speckeys' wait and hands F1 back; speckeys reads that F1
    # as a key, stops the speech and ends with F1 too (GAME_SPEC 8.1 last bullet but one).
    rig = Rig([F5, ("cut", 0.5, F6)], speech_per_char=SPEECH)
    rig.game.pause_log = []
    assert run_key(rig) == "112"
    assert events(rig) == [("stop", ""), ("speak", H.SPECIAL_KEYS), ("speak", words.KEYS_ADDED_F9), ("stop", ""), ("speak", H.GAME_INSTRUCTIONS),
                           ("speak", H.FOOTBALL_INSTRUCTIONS), ("stop", ""), ("stop", "")]
    assert rig.game.hotkeys.runs == ["116", "117"]
    assert rig.game.pause_log == [(0x42028d, 0.3)]


# ----- F6, readins -----

def test_f6_reads_both_parts_with_the_pause_between_them():
    rig = Rig([F6], speech_per_char=SPEECH)
    rig.game.pause_log = []
    assert run_key(rig) == "112"
    assert events(rig) == [("stop", ""), ("speak", H.GAME_INSTRUCTIONS), ("speak", H.FOOTBALL_INSTRUCTIONS),
                           ("stop", "")]
    assert rig.game.pause_log == [(0x42028d, 0.3)]
    assert H.GAME_INSTRUCTIONS.startswith("Game instructions. You will first be asked to choose the voices")
    assert len(H.FOOTBALL_INSTRUCTIONS_PIECES) == 23 and H.FOOTBALL_INSTRUCTIONS_JOINER == " "


def test_f1_during_part_one_starts_it_again():
    rig = Rig([F6, ("cut", 0.5, F1)], speech_per_char=SPEECH)
    assert run_key(rig) == "112"
    assert events(rig) == [("stop", ""), ("speak", H.GAME_INSTRUCTIONS), ("stop", ""), ("stop", ""),
                           ("speak", H.GAME_INSTRUCTIONS), ("speak", H.FOOTBALL_INSTRUCTIONS), ("stop", "")]


def test_escape_during_part_one_ends_the_menu():
    rig = Rig([F6, ("cut", 0.5, ESC)], speech_per_char=SPEECH)
    rig.game.pause_log = []
    assert run_key(rig) == "112"
    assert events(rig) == [("stop", ""), ("speak", H.GAME_INSTRUCTIONS), ("stop", ""), ("stop", "")]
    assert rig.game.pause_log == []


def test_another_key_during_part_one_goes_to_part_two_without_the_pause():
    rig = Rig([F6, ("cut", 0.5, A_KEY)], speech_per_char=SPEECH)
    rig.game.pause_log = []
    assert run_key(rig) == "112"
    assert events(rig) == [("stop", ""), ("speak", H.GAME_INSTRUCTIONS), ("stop", ""),
                           ("speak", H.FOOTBALL_INSTRUCTIONS), ("stop", "")]
    assert rig.game.pause_log == []


def test_f1_during_part_two_starts_again_at_part_one_and_another_key_ends():
    rig = Rig([F6, ("end",), ("cut", 2.0, F1), ("end",), ("cut", 2.0, A_KEY)], speech_per_char=SPEECH)
    assert run_key(rig) == "112"
    assert events(rig) == [("stop", ""), ("speak", H.GAME_INSTRUCTIONS), ("speak", H.FOOTBALL_INSTRUCTIONS),
                           ("stop", ""), ("stop", ""), ("speak", H.GAME_INSTRUCTIONS),
                           ("speak", H.FOOTBALL_INSTRUCTIONS), ("stop", ""), ("stop", "")]


# ----- F7, SayHints -----

def test_f7_reads_the_terms_and_ends_the_blitz_text_with_play_d014():
    rig = Rig([F7], speech_per_char=SPEECH)
    assert run_key(rig) == "112"
    text = H.TERMINOLOGY + "play."
    assert events(rig) == [("stop", ""), ("speak", text), ("stop", "")]
    assert text.startswith("football terminology. Backfield: The area behind the line of scrimmage.")
    assert text.endswith("the offence may end up with a very long gain on the play.")
    assert len(H.TERMINOLOGY_PIECES) == 63                 # the title, 56 terms, "In Jim's NFL football game.", 5 plays


def test_any_key_during_the_terms_ends_the_menu_f1_too():
    rig = Rig([F7, ("cut", 3.0, F1)], speech_per_char=SPEECH)
    assert run_key(rig) == "112"
    assert events(rig) == [("stop", ""), ("speak", H.TERMINOLOGY + "play."), ("stop", ""), ("stop", "")]


# ----- H12 (nfl4 only): the added help of the extras -----

class HelpRules(ClassicRules):
    def extra_help(self, key):
        return ["Added help for " + key + "."]


@pytest.mark.parametrize("key, last_original", [(F5, words.KEYS_ADDED_F9), (F6, H.FOOTBALL_INSTRUCTIONS),
                                                (F7, H.TERMINOLOGY + "play.")])
def test_h12_lines_follow_the_original_text_and_classic_has_none(key, last_original):
    assert ClassicRules().extra_help(str(key)) == []
    rig = Rig([key], speech_per_char=SPEECH)
    rig.game.rules = HelpRules()
    run_key(rig)
    spoken = [text for kind, text in events(rig) if kind == "speak"]
    assert spoken[-2:] == [last_original, "Added help for %d." % key]


# ----- F8, ctog -----

def test_f8_switches_the_comments_off_and_on_says_so_waited_and_saves_each_time():
    rig = Rig([F8, F8])
    options, saves = with_options(rig)
    assert rig.game.comtog == 0
    assert run_key(rig) == "112"
    assert rig.game.comtog == 1 and options.settings.game.comments is False and saves.count == 1
    assert run_key(rig) == "112"
    assert rig.game.comtog == 0 and options.settings.game.comments is True and saves.count == 2
    assert events(rig) == [("stop", ""), ("speak", T.COMMENTS_OFF), ("wait", ""), ("stop", ""),
                           ("stop", ""), ("speak", T.COMMENTS_ON), ("wait", ""), ("stop", "")]


# ----- Ctrl, adjrate -----

def test_ctrl_changes_the_rate_speaks_the_number_and_saves_on_enter():
    rig = Rig([CTRL, UP, UP, DOWN, A_KEY, ENTER])
    options, saves = with_options(rig, base_rate=0)
    assert run_key(rig) == "112"
    got = [(kind, text) for kind, text in rig.sapi.events if kind in ("speak", "stop", "rate")]
    assert got == [("stop", ""), ("rate", 0), ("speak", T.RATE_PROMPT), ("speak", "0"),
                   ("rate", 1), ("stop", ""), ("speak", "1"),
                   ("rate", 2), ("stop", ""), ("speak", "2"),
                   ("rate", 1), ("stop", ""), ("speak", "1"),
                   ("rate", 1), ("speak", T.RATE_PROMPT), ("speak", "1"),       # any other key: the instruction again
                   ("stop", "")]
    assert options.settings.speech.rate == 1 and saves.count == 1
    assert rig.game.vr == 1                                  # rady's counter follows (G-S4)


def test_the_rate_starts_at_the_voices_own_rate_and_stays_in_minus_10_to_10():
    rig = Rig([CTRL, UP, ENTER, CTRL, DOWN, ENTER])
    options, saves = with_options(rig, base_rate=10)
    run_key(rig)
    assert options.settings.speech.rate == 10
    options.settings.speech.rate = -10
    run_key(rig)
    assert options.settings.speech.rate == -10
    numbers = [text for kind, text in rig.sapi.events if kind == "speak" and text != T.RATE_PROMPT]
    assert numbers == ["10", "10", "-10", "-10"]
    assert saves.count == 2


# ----- F11, adjvol -----

def volume_prompt(role):
    return T.VOLUME_PROMPT_START + F11_NAMES[role] + T.VOLUME_PROMPT_MIDDLE + T.VOLUME_PROMPT_END


SOUND_PROMPT = T.SOUND_PROMPT_START + T.SOUND_PROMPT_MIDDLE + T.SOUND_PROMPT_END


def test_f11_sets_the_five_voice_volumes_each_in_its_own_voice_then_the_sound_volume(tmp_path):
    answers = [F11,
               UP, UP, ENTER,                       # the announcer: 95 + 5 = 100 is the maximum, again the maximum
               DOWN, F1, "x", ENTER,                # your quarterback: 90; F1 and another key speak the prompt again
               ENTER, ENTER, ENTER,                 # your punter, your opponents quarterback, your opponents punter
               UP, DOWN, ENTER]                     # the sounds: 0 + 100 is the maximum, then -100
    rig = Rig(answers, sounds_dir=tmp_path)
    rig.keys.hint_enabled = True                         # S8.2: this test pins the hint too
    options, saves = with_options(rig)
    assert run_key(rig) == "112"
    assert rig.said == [
        (volume_prompt(ANNOUNCER), ANNOUNCER, 0), (T.VOLUME_MAXIMUM, ANNOUNCER, 0), (T.VOLUME_MAXIMUM, ANNOUNCER, 0),
        (volume_prompt(OWN_QUARTERBACK), OWN_QUARTERBACK, 0), (T.VOLUME_LOWER, OWN_QUARTERBACK, 0),
        (volume_prompt(OWN_QUARTERBACK), OWN_QUARTERBACK, 0),                 # F1: no echo (saykey is not called)
        (words.F1_HELP_HINT, OWN_QUARTERBACK, 0),                              # S8.2: then where the help is, in the voice that spoke
        ("x", OWN_QUARTERBACK, 0), (volume_prompt(OWN_QUARTERBACK), OWN_QUARTERBACK, 0),
        (volume_prompt(OWN_PUNTER), OWN_PUNTER, 0),
        (volume_prompt(OPPONENT_QUARTERBACK), OPPONENT_QUARTERBACK, 0),
        (volume_prompt(OPPONENT_PUNTER), OPPONENT_PUNTER, 0),
        (SOUND_PROMPT, ANNOUNCER, 0), (T.VOLUME_MAXIMUM, ANNOUNCER, 0), (T.VOLUME_LOWER, ANNOUNCER, 0)]
    assert options.volume(ANNOUNCER) == 100 and options.volume(OWN_QUARTERBACK) == 90
    assert options.volume(OWN_PUNTER) == 95
    assert ("role_volume", "announcer=100") in rig.sapi.events
    assert ("role_volume", "own_quarterback=90") in rig.sapi.events
    assert options.wavol == -100 and rig.sounds.wavol == -100      # the sound procedures read the same setting
    assert saves.count == 1
    assert [e.sound_id for e in rig.slot_log if e.action == "play"].count("snd_foot0") == 2   # the demo, each change


def test_a_voice_volume_reaches_its_minimum_at_zero():
    rig = Rig([F11] + [DOWN] * 19 + [ENTER] * 5 + [ENTER])
    options, _ = with_options(rig)
    run_key(rig)
    said = [text for text, _, _ in rig.said]
    assert said[1:19] == [T.VOLUME_LOWER] * 18 and said[19] == T.VOLUME_MINIMUM     # 95 - 18 x 5 = 5, then 0
    assert options.volume(ANNOUNCER) == 0


def test_the_crowd_levels_come_from_their_base_values_not_counted_twice_d023(tmp_path):
    rig = Rig([F11] + [ENTER] * 5 + [UP, ENTER], sounds_dir=tmp_path)
    options, _ = with_options(rig)
    options.set_wavol(-1000)
    rig.sounds.start_crowds()                     # both beds at -1200 + wavol = -2200 (the menus' level)
    run_key(rig)
    assert options.wavol == -900
    # the original: crowd 1 = (-100 - 1000) + -900 = -2000 after Up, and -1200 - 1000 - 900 at Enter for crowd 2
    assert rig.audio.volume(SLOT_CROWD1) == -1200 + -900          # Enter: crwd1 + wavol
    assert rig.audio.volume(SLOT_CROWD2) == -1200 + -900          # Enter: the level before the ramp, its wavol new
    assert rig.audio.volume(SLOT_HIKE) == -1600 + -900            # MakeHike's level with the new wavol
    crowd1 = [e.volume for e in rig.slot_log if e.action == "volume" and e.slot == SLOT_CROWD1]
    assert crowd1 == [-1100, -1000, -2100]        # -100 + the entry wavol, -100 + the new wavol, crwd1 + wavol
    crowd2 = [e.volume for e in rig.slot_log if e.action == "volume" and e.slot == SLOT_CROWD2]
    assert crowd2 == list(range(-2200, -999, 100)) + [-900, -2100]    # c2uf in 13 steps, full, back to its base


def test_the_sound_volume_says_lower_at_exactly_minus_5000_and_minimum_below(tmp_path):
    rig = Rig([F11] + [ENTER] * 5 + [DOWN, DOWN, ENTER], sounds_dir=tmp_path)
    options, _ = with_options(rig)
    options.set_wavol(-4900)
    run_key(rig)
    said = [text for text, _, _ in rig.said]
    assert said[-2:] == [T.VOLUME_LOWER, T.VOLUME_MINIMUM]
    assert options.wavol == -5000


# ----- F12, the voice picker per speaker (G-S8) -----

class Catalog:
    def __init__(self, voices):
        self.list = voices

    def voices(self, timeout=None):
        return list(self.list)


VOICES = [VoiceInfo(0, "id0", "Alpha", "EngA"), VoiceInfo(1, "id1", "Beta", "EngA"), VoiceInfo(2, "id2", "Gamma", "EngB")]


def test_f12_asks_each_speaker_in_the_original_order_and_saves():
    answers = [F12,
               DOWN, ENTER, ENTER,          # announcer: engine list opens on EngA; Down to EngB, its one voice Gamma
               ESC,                         # your quarter back: keeps its voice
               ENTER, DOWN, ENTER,          # opponent's quarter back: EngA, Beta
               ENTER, ESC, ESC,             # your punter: into EngA and back out, then out of the engines: kept
               HOME, ENTER, ENTER]          # opponent's punter: all voices, Alpha = SAPI's first voice
    rig = Rig(answers)
    options, saves = with_options(rig)
    options.voice_catalog = Catalog(VOICES)
    sexes = []
    rig.game.get_sex_of = lambda: sexes.append(1)
    assert run_key(rig) == "112"
    assert options.settings.speech.voices == {ANNOUNCER: "id2", OWN_QUARTERBACK: None, OPPONENT_QUARTERBACK: "id1",
                                              OWN_PUNTER: None, OPPONENT_PUNTER: None}
    assert [e for e in rig.sapi.events if e[0] == "role_voice"] == [
        ("role_voice", "announcer=id2"), ("role_voice", "opponent_quarterback=id1"), ("role_voice", "opponent_punter=")]
    samples = [(text, role) for text, role, _ in rig.said if "This is how this voice will speak" in text]
    sample = " This is how this voice will speak in N. F. L. football."
    assert samples == [("Voice set to Gamma." + sample, ANNOUNCER), ("Voice set to Beta." + sample, OPPONENT_QUARTERBACK),
                       ("Voice set to Alpha." + sample, OPPONENT_PUNTER)]
    titles = [text.split(".")[0] for text, _, _ in rig.said if text.startswith("Choose the voice for")]
    assert titles == ["Choose the voice for the announcer", "Choose the voice for your quarterback",
                      "Choose the voice for your opponents quarterback", "Choose the voice for your punter",
                      "Choose the voice for your punter",            # back from EngA's voices to the engines
                      "Choose the voice for your opponents punter"]
    assert saves.count == 1 and sexes == [1]


def test_f12_with_one_voice_hands_f1_back_at_once_q59_not_reproduced():
    rig = Rig([F12])
    options, saves = with_options(rig)
    options.voice_catalog = Catalog(VOICES[:1])
    assert run_key(rig) == "112"
    assert events(rig) == [("stop", "")]           # only getkey's: nothing spoken, nothing saved
    assert saves.count == 0


def test_f12_during_a_game_gives_the_running_game_its_new_he_and_she_words():
    rig = Rig([])
    calls = []

    class Engine:
        def get_sex_of(self):
            calls.append(1)
    rig.game.get_sex_of()
    rig.game.play_engine = Engine()
    rig.game.get_sex_of()
    assert calls == [1]


def test_the_hot_keys_follow_a_key_input_the_rig_swaps_in():
    rig = Rig([])
    keys = type(rig.keys)(rig.clock, [F8])
    rig.game.keys = keys
    rig.keys = keys
    assert keys.key_handler == rig.game.hotkeys.dispatch
    assert run_key(rig) == "112" and rig.game.hotkeys.runs == ["119"]
