"""The stadium sounds of the N. F. L. rules (nfl4 only, rule 0.13; SY.2, D-102). This is inspired by Jim Kitchen.

About twenty generated sounds in assets/sounds_nx/ are played on the extra channel at moments the game already knows. The properties that
matter: a game plays out identically with them on and off (the stadium draws only from its own generator, nothing waits for a sound); each event
picks the right sound; the player's files replace the shipped ones and numbered files add to a family (rule 0.14); the switch works; Classic never
calls the stadium.
"""
import os
import types
import wave

import pytest

from nfl4.data import settingsfile
from nfl4.data.settings import Settings
from nfl4.extras import stadium as ST
from nfl4.extras.nfl_rules import NflRules, rules_from_settings
from nfl4.game import outcome as O
from nflrig import RecordingRules, sim_game


def test_every_stadium_sound_is_shipped_as_a_short_quiet_enough_wav():
    folder = ST.shipped_folder()
    for name in ST.NAMES:
        path = os.path.join(folder, name + ".wav")
        assert os.path.exists(path), name
        with wave.open(path, "rb") as w:
            assert (w.getnchannels(), w.getsampwidth(), w.getframerate()) == (1, 2, 22050)
            seconds = w.getnframes() / w.getframerate()
            data = w.readframes(w.getnframes())
        assert 0.2 <= seconds <= 4.0, (name, seconds)
        samples = memoryview(data).cast("h")
        assert max(abs(s) for s in samples) < 32767 and any(abs(s) > 3000 for s in samples), name
        assert -2600 <= ST.LEVELS[name] <= -1500, name            # under the speech: -15 to -26 dB under the sound volume


def test_a_players_file_replaces_the_shipped_one_and_a_new_number_adds_to_the_family(tmp_path):
    shipped, mine = tmp_path / "shipped", tmp_path / "mine"
    shipped.mkdir()
    mine.mkdir()
    for n in ("crowd_cheer.wav", "crowd_roar.wav"):
        (shipped / n).write_bytes(b"x")
    (mine / "crowd_cheer.wav").write_bytes(b"y")             # replaces
    (mine / "crowd_cheer2.wav").write_bytes(b"y")            # adds
    (mine / "crowd_cheer15.wav").write_bytes(b"y")
    (mine / "crowd_roar.mp3").write_bytes(b"y")              # not a wav: ignored
    files = ST.family("crowd_cheer", (str(mine), str(shipped)))
    assert [os.path.basename(f) for f in files] == ["crowd_cheer.wav", "crowd_cheer2.wav", "crowd_cheer15.wav"]
    assert files[0].startswith(str(mine))
    assert [os.path.basename(f) for f in ST.family("crowd_roar", (str(mine), str(shipped)))] == ["crowd_roar.wav"]
    assert ST.family("crowd_roar", (str(mine), str(shipped)))[0].startswith(str(shipped))
    assert ST.family("nothing", (str(mine), str(shipped))) == []


class Recorder:
    def __init__(self):
        self.calls = []

    def play_effect(self, path, level=0):
        self.calls.append((os.path.basename(path)[:-4], level))


def stadium_with(seed=1):
    import random

    from nfl4.game.rnd import GameRandom
    st = ST.Stadium(NflRules(), on=True)
    game = types.SimpleNamespace(sounds=Recorder(), rnd=GameRandom(random.Random(seed)), play_engine=types.SimpleNamespace(rules=st.rules))
    game.rnd.seed = seed
    st.attach(game, None)
    return st, game.sounds.calls


def facts(kind, side=1, yards=0, to_go=10, turnover=False, score=None):
    return types.SimpleNamespace(kind=kind, offense=side, yards=yards, to_go=to_go, turnover=turnover, score=score, two_point=False, taken_over=False)


@pytest.mark.parametrize("what, side, expected", [
    (dict(kind=O.INTERCEPTION, turnover=True), 1, "crowd_groan"), (dict(kind=O.FUMBLE, turnover=True), 2, "crowd_roar"),
    (dict(kind=O.SACK), 1, "crowd_groan"), (dict(kind=O.SACK), 2, "crowd_roar"),
    (dict(kind=O.PASS_COMPLETE, yards=31), 1, "crowd_roar"), (dict(kind=O.RUN, yards=22), 2, "crowd_gasp"),
    (dict(kind=O.FIELD_GOAL_MISSED), 1, "crowd_groan"), (dict(kind=O.FIELD_GOAL_SHORT), 2, "crowd_oh"),
    (dict(kind=O.RUN, yards=6, to_go=5), 1, "first_down_chain"), (dict(kind=O.PASS_COMPLETE, yards=11, to_go=10), 2, "first_down_chain"),
])
def test_the_crowd_answers_the_last_play(what, side, expected):
    st, calls = stadium_with()
    st.between(None, facts(side=side, **what))
    assert [name for name, level in calls] == [expected]


def test_a_short_gain_a_score_or_a_play_a_penalty_took_over_makes_no_answer():
    st, calls = stadium_with()
    st.between(None, facts(O.RUN, yards=3, to_go=10))
    st.between(None, facts(O.PASS_COMPLETE, yards=40, score="touchdown"))
    taken = facts(O.SACK)
    taken.taken_over = True
    st.between(None, taken)
    st.between(None, None)
    assert calls == []


def test_the_impacts_and_the_catch_at_the_end_of_the_narration():
    st, calls = stadium_with()
    quiet = types.SimpleNamespace(two_point_try=False)
    st.note_outcome(None, types.SimpleNamespace(kind=O.SACK, yards=-7, two_point_try=False))
    st.note_outcome(None, types.SimpleNamespace(kind=O.RUN, yards=9, two_point_try=False))
    st.note_outcome(None, types.SimpleNamespace(kind=O.PASS_COMPLETE, yards=14, two_point_try=False))
    st.note_outcome(None, types.SimpleNamespace(kind=O.RUN, yards=2, two_point_try=False))
    st.note_outcome(None, types.SimpleNamespace(kind=O.SACK, yards=-5, two_point_try=True))      # a two-point try: nothing
    assert [name for name, level in calls] == ["hit_helmet", "hit_pads", "hit_pads"]
    assert quiet.two_point_try is False


def test_scores_quarters_half_time_and_penalties():
    st, calls = stadium_with()
    state = types.SimpleNamespace(wisoff=1, points=6)
    st.moment(state, "touchdown")
    state.points = 3
    st.moment(state, "score")
    state.wisoff = 2
    st.moment(state, "score")
    st.moment(state, "touchdown")
    state.points = 1
    st.moment(state, "score")
    for quarter in (1, 2, 3, 4):
        st.moment(state, "quarter_end", quarter)
    st.moment(state, "half_time")
    st.moment(state, "two_minute")
    st.penalty(state, 1)
    st.penalty(state, 2)
    assert [name for name, level in calls] == ["crowd_cheer", "crowd_applause", "crowd_oh", "crowd_groan", "crowd_applause", "crowd_applause",
                                               "crowd_applause", "crowd_boo", "flag_throw"]


def test_the_stadium_is_silent_when_off_and_without_sounds():
    st, calls = stadium_with()
    st.on = False
    st.moment(types.SimpleNamespace(wisoff=1, points=6), "touchdown")
    assert calls == []
    st.on = True
    st.game.sounds = None
    st.moment(types.SimpleNamespace(wisoff=1, points=6), "touchdown")


def test_a_family_with_several_files_draws_among_them_with_its_own_generator(tmp_path):
    st, calls = stadium_with(5)
    for n in ("crowd_cheer.wav", "crowd_cheer2.wav", "crowd_cheer3.wav"):
        (tmp_path / n).write_bytes(b"x")
    st.folders = (str(tmp_path),)
    before = st.game.rnd.draws
    for _ in range(30):
        st.play("crowd_cheer")
    assert {name for name, level in calls} == {"crowd_cheer", "crowd_cheer2", "crowd_cheer3"}
    assert st.game.rnd.draws == before                         # the GAME's generator was never asked


def whole_game(tmp_path, seed, on):
    rules = RecordingRules(penalties_on=True, onside_on=True, qb_on=True, challenges_on=True, playbooks_on=True, stadium_on=on)
    from nfl4.game import sounds as game_sounds
    played = []
    real = game_sounds.GameSounds.play_effect
    game_sounds.GameSounds.play_effect = lambda self, path, level=0: played.append(os.path.basename(path)) or real(self, path, level)
    try:
        rig, engine, rules, result = sim_game(tmp_path, seed, rules=rules, trace=True)
    finally:
        game_sounds.GameSounds.play_effect = real
    return rig, played, result


def test_the_stadium_does_not_move_a_single_draw_or_the_result_of_a_game(tmp_path):
    rig_on, played_on, result_on = whole_game(tmp_path / "on", 21, True)
    rig_off, played_off, result_off = whole_game(tmp_path / "off", 21, False)
    assert played_off == [] and len(played_on) > 20
    assert rig_on.rnd.trace == rig_off.rnd.trace and rig_on.rnd.draws == rig_off.rnd.draws and result_on.scores == result_off.scores
    assert {"crowd_cheer.wav", "hit_pads.wav", "first_down_chain.wav"} <= set(played_on)


def test_the_settings_and_the_programs_rules_follow_the_stadium_switch():
    settings = Settings.defaults()
    assert settings.game.nx_stadium is True and rules_from_settings(settings.game).stadium.on is True
    settings.game.nx_stadium = False
    text = settingsfile.render(settings)
    assert "nx_stadium = off" in text
    again, problems = settingsfile.parse(text)
    assert problems == [] and again.game.nx_stadium is False
    rules = rules_from_settings(again.game)
    assert rules.stadium.on is False and rules.for_game().stadium.on is False
    old, problems = settingsfile.parse("# NFL Football 4 settings, format 1\nrules = nfl\n")
    assert old.game.nx_stadium is True
