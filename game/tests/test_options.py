"""Options: the values the hot keys change and where they are saved. This is inspired by Jim Kitchen.

GAME_SPEC 4.5 to 4.8 and 12, D-022 item 3 (the rate in -10 to 10), G-S4 (vr with NVDA and JAWS), G-F8 (settings.txt in
place of footbal0.dat and football.vol), G-S8 (voices as ids).
"""
import logging

from gamerig import Rig
from nfl4.data.settings import Settings
from nfl4.game.options import Options
from nfl4.speech.roles import ANNOUNCER, OWN_PUNTER


class Guard:
    def __init__(self):
        self.forgotten = []

    def forget(self, voice_id):
        self.forgotten.append(voice_id)


def test_vr_is_the_saved_rate_or_the_first_voices_own_rate_kept_in_range():
    rig = Rig([])
    options = Options(Settings.defaults(), rig.speech, base_rate=lambda: 4)
    assert options.vr == 4                                   # "original": the voice's own rate (GAME_SPEC 3 step 3)
    options.settings.speech.rate = 12
    assert options.vr == 10
    assert options.set_vr(-15) == -10 and options.settings.speech.rate == -10
    assert ("rate", -10) in rig.sapi.events


def test_a_failing_base_rate_is_logged_and_counts_as_zero(caplog):
    def broken():
        raise RuntimeError("no voice")
    options = Options(None, Rig([]).speech, base_rate=broken)
    with caplog.at_level(logging.WARNING):
        assert options.vr == 0
    assert any("own rate could not be read" in r.message for r in caplog.records)


def test_comtog_is_1_when_the_comments_are_off():
    options = Options(None, Rig([]).speech)
    assert options.comtog == 0
    options.set_comtog(1)
    assert options.settings.game.comments is False and options.comtog == 1


def test_volumes_and_the_sound_level_are_kept_in_their_ranges_and_reach_the_speaker():
    rig = Rig([])
    options = Options(None, rig.speech)
    assert options.set_volume(ANNOUNCER, 120) == 100 and options.set_volume(OWN_PUNTER, -5) == 0
    assert ("role_volume", "announcer=100") in rig.sapi.events and ("role_volume", "own_punter=0") in rig.sapi.events
    assert options.set_wavol(100) == 0 and options.set_wavol(-6000) == -5000
    assert options.settings.audio.sound_level == -5000


def test_a_chosen_voice_is_saved_by_id_and_a_set_aside_voice_gets_another_try():
    rig = Rig([])
    guard = Guard()
    options = Options(None, rig.speech, voice_guard=guard)
    options.set_voice(OWN_PUNTER, "id7")
    options.set_voice(ANNOUNCER, None)
    assert options.voice(OWN_PUNTER) == "id7" and options.voice(ANNOUNCER) is None
    assert guard.forgotten == ["id7"]
    assert ("role_voice", "own_punter=id7") in rig.sapi.events


def test_a_save_that_fails_never_stops_the_game(caplog):
    def broken():
        raise OSError("disk gone")
    options = Options(None, Rig([]).speech, save=broken)
    with caplog.at_level(logging.WARNING):
        options.save()
    assert any("saving the settings failed" in r.message for r in caplog.records)


def test_the_game_reads_vr_and_comtog_from_its_options_and_shares_the_sound_level(tmp_path):
    rig = Rig([], sounds_dir=tmp_path)
    game = rig.game
    assert game.vr == 0 and game.comtog == 0                 # the defaults the earlier sessions' tests rely on
    game.options.set_vr(5)
    game.options.set_comtog(1)
    assert game.vr == 5 and game.comtog == 1
    game.options.set_wavol(-700)
    assert rig.sounds.wavol == -700                          # one AudioSettings for the menus and the sounds
