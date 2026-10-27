"""The radio-style broadcast of the N. F. L. rules (nfl4 only, rule 0.13; CLAUDE.md 0.27; playbook 7.19; SY.1, D-101).
This is inspired by Jim Kitchen.

The color analyst (his own voice, his own random generator, fifty lines of pools by moment) and the pools of remarks.txt the broadcast uses
(BN, ASK and the analyst's). BC.2 (D-180): the original's banter step is gone from every mode, and with it the pool BN drawn by the original's
rule on the game's generator (the Rules hook H23 banter_lines); BC.3 draws BN on the broadcast's own generator. The properties that matter:
the draws of the game are the same with the broadcast on and off (the analyst draws only from his own generator); F8 silences him; the pools
follow the text rules of the playbook; a player can change, switch off or add a line.
"""
import re

import pytest

from gamerig import Rig
from nfl4.data import customlists as cl
from nfl4.data import settingsfile
from nfl4.data.settings import Settings
from nfl4.extras import broadcast as BC
from nfl4.extras import nx_texts as X
from nfl4.extras import remarks as RM
from nfl4.extras.nfl_rules import NflRules, rules_from_settings
from nfl4.game.rules import CLASSIC, ClassicRules
from nfl4.speech.roles import ALL_ROLES, ANNOUNCER, COLOR, ROLES
from nflrig import RecordingRules, sim_game

COLOR_POOLS = RM.COLOR_POOLS
SIZES = {"BN": 142, "ASK": 12, "CKO": 8, "CBG": 10, "CSK": 10, "CTV": 10, "CTD": 10, "CFG": 8, "CFM": 8, "CTC": 8, "CTS": 8, "CFD": 8, "CRZ": 8,
         "CPN": 8, "CTM": 8, "CQE": 8, "CHT": 8, "CFN": 8, "CFT": 6, "CTT": 8, "CBO": 8}


# ----- the texts -----

def test_the_pools_have_their_lines_with_the_ids_the_customization_expects():
    assert set(SIZES) == set(RM.BROADCAST_POOLS)
    for pool, size in SIZES.items():
        lines = RM.DEFAULT_POOLS.lines(pool)
        assert [r.number for r in lines] == list(range(1, size + 1)), pool
        assert [r.id for r in lines] == [RM.remark_id(pool, n) for n in range(1, size + 1)]
    assert RM.DEFAULT_POOLS.lines("BN")[99].id == "BN100" and RM.DEFAULT_POOLS.lines("BN")[8].id == "BN09"


def test_every_line_of_the_broadcast_follows_the_text_rules_of_the_playbook():
    seen = {}
    for pool in RM.BROADCAST_POOLS:
        for remark in RM.DEFAULT_POOLS.lines(pool):
            text = X.TEXTS[remark.id].strip()
            assert text.isascii() and 1 < len(text) <= 150, remark.id
            assert not re.search(r"[\[\]]", text) and "  " not in text, remark.id
            assert not re.search(r"\d", text), remark.id                  # numbers are said as words (a placeholder carries the digits)
            known = RM.PLACEHOLDERS[pool]
            assert all(p in known for p in re.findall(r"<[^<>]+>", text)), (remark.id, known)
            assert text not in seen, (remark.id, seen.get(text))
            seen[text] = remark.id
            assert X.SPEAKERS[remark.id] == ("color" if pool in COLOR_POOLS else "say")


def test_the_radio_banter_lines_are_generic():
    # the radio lines are generic: no placeholder, no sound, no name of a team or a person of the game
    assert all(X.TEXTS[r.id].replace("<commentator>", "") .count("<") == 0 and "[" not in X.TEXTS[r.id] for r in RM.DEFAULT_POOLS.lines("BN"))     # SZ.1: only the commentator's name
    assert not any("Kitchen" in X.TEXTS[r.id] or "Jim" in X.TEXTS[r.id] for r in RM.DEFAULT_POOLS.lines("BN"))


def test_the_remark_ids_are_not_the_old_banter_ids():
    assert RM.parse_id("BN142") == ("BN", 142) and RM.parse_id("bn7") == ("BN", 7) and RM.parse_id("B007") is None
    assert RM.remark_id("BN", 7) == "BN07" and RM.remark_id("CTD", 3) == "CTD03"


# ----- the original's banter step is gone (BC.2) -----

def test_neither_rules_has_the_hook_of_the_originals_banter_lines():
    assert not hasattr(CLASSIC, "banter_lines") and not hasattr(NflRules(), "banter_lines")
    assert not hasattr(BC.Broadcast(NflRules()), "banter_lines") and not hasattr(BC.Broadcast(NflRules()), "radio_banter")


# ----- the analyst in whole games -----

def whole_game(tmp_path, seed, on):
    said = []
    rules = RecordingRules(penalties_on=True, onside_on=True, qb_on=True, challenges_on=True, playbooks_on=True, broadcast_on=on)
    from nfl4.game import flow
    real = flow.Game.say_role
    flow.Game.say_role = lambda self, text, role: said.append((role, text)) or real(self, text, role)
    try:
        rig, engine, rules, result = sim_game(tmp_path, seed, rules=rules, trace=True)
    finally:
        flow.Game.say_role = real
    return rig, engine, said, result


def test_the_analyst_does_not_move_a_single_draw_or_the_result_of_a_game(tmp_path):
    rig_on, _e, said_on, result_on = whole_game(tmp_path / "on", 21, True)
    rig_off, _e2, said_off, result_off = whole_game(tmp_path / "off", 21, False)
    assert said_off == [] and len(said_on) > 5
    assert rig_on.rnd.trace == rig_off.rnd.trace and rig_on.rnd.draws == rig_off.rnd.draws
    assert result_on.scores == result_off.scores


def test_the_analyst_speaks_in_his_own_voice_after_the_opening_and_the_lines_are_those_of_his_pools(tmp_path):
    rig, engine, said, result = whole_game(tmp_path, 22, True)
    assert all(role == COLOR for role, _ in said)
    patterns = [re.sub(r"<[a-z ]+>", ".+", re.escape(X.TEXTS[r.id].strip())) for pool in COLOR_POOLS for r in RM.DEFAULT_POOLS.lines(pool)]
    for _role, text in said:
        body = text.strip()
        assert not re.search(r"<[^<>]+>", body), body                       # every placeholder is filled
        assert any(re.fullmatch(pattern, body) for pattern in patterns), body
    touchdown = [re.sub(r"<[a-z ]+>", ".+", re.escape(X.TEXTS[r.id].strip())) for r in RM.DEFAULT_POOLS.lines("CTD")]
    assert any(re.fullmatch(pattern, text.strip()) for _role, text in said for pattern in touchdown)        # a game has touchdowns: the analyst is there


def test_the_same_seed_gives_the_same_commentary_and_another_seed_another(tmp_path):
    a = whole_game(tmp_path / "a", 31, True)[2]
    b = whole_game(tmp_path / "b", 31, True)[2]
    c = whole_game(tmp_path / "c", 32, True)[2]
    assert a == b and a != c


def test_the_analyst_leaves_two_plays_between_his_ordinary_lines_and_is_in_every_game_at_the_big_moments(tmp_path):
    rig, engine, said, result = whole_game(tmp_path, 23, True)
    texts = [t for _r, t in said]
    assert 8 <= len(texts) <= 60, len(texts)                                  # a radio crew fills the gaps, it does not talk over the game
    rig2, engine2, said2, result2 = whole_game(tmp_path / "again", 24, True)
    assert any("half" in t.lower() for t in [t for _r, t in said2] + texts)   # the halftime line is certain (CHT 100 percent)


def test_f8_switches_the_analyst_off(tmp_path):
    said = []
    rules = RecordingRules(penalties_on=True, qb_on=True, playbooks_on=True, broadcast_on=True)
    from nfl4.game import flow
    real = flow.Game.say_role
    flow.Game.say_role = lambda self, text, role: said.append(text)
    try:
        import random
        from pagrig import make_rig
        from nflrig import SimEngine, QUARTERBACKS
        rig = make_rig(tmp_path, rng=random.Random(41), fast=True, vtrnt=2, gtp=1)
        rig.game.comtog_source = lambda: 1
        engine = SimEngine(rig.game, rules, quarterback_names=lambda state: QUARTERBACKS, own_names=None, opponent_names=None)
        rig.game.play_engine = engine
        try:
            engine.run()
        finally:
            rig.game.play_engine = None
    finally:
        flow.Game.say_role = real
    assert said == []


def test_the_intro_of_the_analyst_is_said_once_per_program_run_by_the_announcer(tmp_path):
    rig, engine, said, result = whole_game(tmp_path, 25, True)
    assert rig.game.analyst_introduced is True
    spoken = [t for t, role, step in rig.said]
    assert spoken.count(X.text("NXB-B01", commentator="Gus Delgado")) == 1          # SZ.1: the name is filled in (BC.2: the made-up default)
    assert not any("Ghip" in t for t in spoken)


def test_a_players_own_line_and_off_for_the_analysts_pools(tmp_path):
    problems = cl.Problems("remarks.txt")
    pools = RM.build_pools({"CTD01": None, "CTD11": "<team> score, says <coach>", "CTD12": "oops <nothing>"}, problems)
    assert [r.id for r in pools.lines("CTD")][0] == "CTD02" and pools.lines("CTD")[-1].id == "CTD12"
    assert [key for key, _ in problems.items] == ["CTD11", "CTD12"]          # <coach> is not in the CTD pool, nor is <nothing>: spoken as written
    assert RM.PLACEHOLDERS["CTD"] == ("<team>", "<opponent>", "<situation>", "<commentator>")      # SZ.1: the name fits every pool


# ----- the voice and the settings -----

def test_the_analyst_is_a_sixth_speaker_outside_the_five_of_the_original():
    assert COLOR == "color" and COLOR not in ROLES and ALL_ROLES == ROLES + (COLOR, "referee")           # SY.3 added the referee
    settings = Settings.defaults()
    assert set(settings.speech.voices) == set(ALL_ROLES) and settings.speech.volumes[COLOR] == 95
    assert settings.game.nx_broadcast is True


def test_the_settings_file_keeps_the_analysts_voice_volume_and_the_broadcast_switch():
    settings = Settings.defaults()
    settings.speech.voices[COLOR] = "voice-id-7"
    settings.speech.volumes[COLOR] = 60
    settings.game.nx_broadcast = False
    text = settingsfile.render(settings)
    assert "voice_color = voice-id-7" in text and "volume_color = 60" in text and "nx_broadcast = off" in text
    again, problems = settingsfile.parse(text)
    assert problems == [] and again.speech.voices[COLOR] == "voice-id-7" and again.speech.volumes[COLOR] == 60
    assert again.game.nx_broadcast is False
    old, problems = settingsfile.parse("# NFL Football 4 settings, format 1\nrules = nfl\n")
    assert problems == [] and old.game.nx_broadcast is True               # a file from before SY.1: the broadcast is on


def test_the_programs_rules_follow_the_setting():
    settings = Settings.defaults()
    rules = rules_from_settings(settings.game)
    assert rules.broadcast.analyst is True and rules.broadcast.commentator == "Gus Delgado"
    settings.game.nx_broadcast = False
    rules = rules_from_settings(settings.game)
    assert rules.broadcast.analyst is False and rules.for_game().broadcast.analyst is False
    settings.game.rules = "classic"
    assert rules_from_settings(settings.game) is CLASSIC


def test_classic_answers_the_broadcast_hooks_with_nothing():
    rules = ClassicRules()
    assert rules.broadcast_moment(object(), "score") is None


class Catalog:
    loaded = True

    def __init__(self, voices):
        self._voices = voices

    def voices(self, timeout=0.0):
        return self._voices

    def load_async(self, refresh=False):
        pass


def test_the_analyst_gets_a_voice_of_his_own_when_the_player_has_not_chosen_one(tmp_path):
    from nfl4.game.options import Options
    from nfl4.speech.voices import VoiceInfo
    rig = Rig([], sounds_dir=tmp_path)
    voices = [VoiceInfo(0, "id0", "Alpha", "EngA"), VoiceInfo(1, "id1", "Beta", "EngB"), VoiceInfo(2, "id2", "Gamma", "EngA"),
              VoiceInfo(3, "id3", "Delta", "EngA")]
    saves = []
    options = Options(Settings.defaults(), rig.speech, save=lambda: saves.append(1), base_rate=lambda: 0, voice_catalog=Catalog(voices))
    rig.game.options = options
    b = BC.Broadcast(NflRules(), analyst=True)
    b.game = rig.game
    b._own_voice()
    assert options.voice(COLOR) == "id2" and options.voice("referee") == "id3" and saves == [1]     # the announcer's engine, the next voices
    assert ("role_voice", "color=id2") in rig.sapi.events
    options.set_voice(COLOR, "id1")
    b._own_voice()
    assert options.voice(COLOR) == "id1"                               # the player's own choice stays
    options.set_voice(COLOR, None)
    options.set_voice("referee", "id3")
    options.voice_catalog = Catalog(voices[:1])
    b._own_voice()
    assert options.voice(COLOR) is None                                # one voice only: the analyst shares it


def test_a_voice_list_that_is_not_read_yet_leaves_the_analyst_with_the_announcers_voice_for_now(tmp_path):
    from nfl4.game.options import Options
    rig = Rig([], sounds_dir=tmp_path)
    started = []

    class Slow(Catalog):
        loaded = False

        def load_async(self, refresh=False):
            started.append(1)
    options = Options(Settings.defaults(), rig.speech, save=lambda: True, base_rate=lambda: 0, voice_catalog=Slow([]))
    rig.game.options = options
    b = BC.Broadcast(NflRules(), analyst=True)
    b.game = rig.game
    b._own_voice()
    assert options.voice(COLOR) is None and started == [1]


# ----- F11 and F12 ask for the analyst only in the N. F. L. rules with the broadcast on -----

F11, F12, ENTER = 122, 123, 13


def f11_roles(tmp_path, rules, broadcast_on):
    from nfl4.game.options import Options
    rig = Rig([F11] + [ENTER] * 10, sounds_dir=tmp_path)
    settings = Settings.defaults()
    settings.audio = rig.sounds.settings
    settings.game.nx_broadcast = broadcast_on
    rig.game.options = Options(settings, rig.speech, save=lambda: True, base_rate=lambda: 0)
    rig.game.rules = rules
    rig.keys.getkey(rig.speech)
    return [role for text, role, step in rig.said if "volume" in text.lower() and role in ALL_ROLES][:]


def test_f11_asks_for_the_analyst_after_the_five_speakers_only_with_the_nfl_rules_and_the_broadcast_on(tmp_path):
    five = f11_roles(tmp_path / "a", CLASSIC, True)
    assert COLOR not in five and ANNOUNCER in five
    six = f11_roles(tmp_path / "b", NflRules(), True)
    assert six[-1] == COLOR or COLOR in six
    off = f11_roles(tmp_path / "c", NflRules(), False)
    assert COLOR not in off


def test_the_analysts_role_name_and_the_originals_names_stay_apart():
    from nfl4.speech.roles import EXTRA_NAMES, F11_NAMES, F12_NAMES, spoken_name
    assert set(F11_NAMES) == set(F12_NAMES) == set(ROLES) and EXTRA_NAMES == {COLOR: "the color commentator", "referee": "the referee"}
    assert spoken_name(COLOR) == "the color commentator" and spoken_name(ANNOUNCER) == F11_NAMES[ANNOUNCER]       # SZ.1: the name is a setting
