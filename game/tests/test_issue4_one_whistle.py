"""GitHub issue 4 (a tester, 2026-11-07: "It uses two different whistles this should be fixed."), fixed in 0.16.18 (D-215, rule 0.40 (4)).
This is inspired by Jim Kitchen.

Whole N. F. L. rules games, with the stadium sounds on and off: every whistle (PlayTackle(8)) plays the one made whistle.wav and nothing
else, so a later code path that plays the original's foot11 or another kind of whistle in the owner's mode fails here. The unit tests of
test_tester_20261106.py check play_tackle alone; this one checks every whistle a game really blows."""
from nfl4.audio.output import SLOT_TACKLE
from nfl4.game import sounds as S

import test_sy3_referee as T


def test_every_whistle_of_whole_nfl_rules_games_is_the_one_made_whistle(tmp_path, monkeypatch):
    real = S.GameSounds.play_tackle
    count = []

    def blown(self, n):
        # flow.Game sets own_mode from settings.game.rules == "nfl" (test_music_celebration_nxm); sim_game builds no flow.Game, so the rig's
        # N. F. L. rules game is told here what the program tells it
        self.own_mode = lambda: True
        real(self, n)
        if n == 8:
            count.append(n)

    monkeypatch.setattr(S.GameSounds, "play_tackle", blown)
    for seed in (3, 21):
        for on in (True, False):
            before = len(count)
            rig, _said, _result = T.whole_game(tmp_path / ("%d_%s" % (seed, on)), seed, on)
            played = [e.sound_id for e in rig.slot_log if e.action == "play" and e.slot == SLOT_TACKLE]
            # the three tackle sounds are the hits: they DO end in the original's own whistle, which the owner's mode cuts off (GitHub issue 6,
            # D-219; tests/test_issue6_tackle_whistle.py checks the cut and the whistle after each); here only the whistles proper are counted
            whistles = {p for p in played if p not in ("snd_foot4", "snd_foot5", "snd_foot6")}
            assert len(count) - before > 20, (seed, on)
            assert whistles == {"file whistle.wav"}, (seed, on, whistles)
