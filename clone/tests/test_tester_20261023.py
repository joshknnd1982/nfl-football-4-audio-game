"""A tester's six bugs of 2026-10-23, forwarded by the owner (nfl4 only, rule 0.13). This is inspired by Jim Kitchen.

1 "you don't hear the referee announcement of a penalty": after the choice the referee says the result (NXP-24 to NXP-28).
2 "the whistle isn't an NFL sounding whistle": every whistle of the N. F. L. rules is the official's (never foot11), and the player's whistle.wav
  replaces them all.
3 "you don't hear crowd reaction when a big play happens or when penalties are called": louder reactions on a channel of their own, a big play
  family and a flag-on-them family, the crowd at the flag, and no reaction for a play a penalty took over.
4 "wrong position players are still playing at running back": tests/test_sx11_names.py (the backs) and tests/test_fr_workload.py (the depth chart).
5 "blitzes rarely get home": the Blitz item sends five or more, and five and six rushers get home more often.
6 "remove the band and sound effects when you start the game and load a saved game": no foot0 and no crowd surge at the start of a game of the
  N. F. L. rules; Classic keeps the original's.
"""
import os
import random
import types

import pytest
from nflrig import RecordingRules, sim_game
from test_sy2_stadium import Recorder, facts, stadium_with

from nfl4.audio.output import CROWD_SLOT, EXTRA_SLOT
from nfl4.extras import nx_texts as X
from nfl4.extras import stadium as ST
from nfl4.extras.nfl_rules import NflRules
from nfl4.extras.playbook_flow import BLITZ_FAMILY, blitz_family_sends_five
from nfl4.extras.plays import catalog as C
from nfl4.extras.plays import model_data as MD
from nfl4.game import outcome as O
from nfl4.game.rules import CLASSIC


# ----- 1: the referee's result -----

def test_the_referee_says_the_result_after_every_choice_in_whole_games(tmp_path):
    said = []
    rules = RecordingRules(penalties_on=True, broadcast_on=True, stadium_on=True)
    from nfl4.game import flow
    real = flow.Game.say_referee
    flow.Game.say_referee = lambda self, text: said.append(text) or real(self, text)
    try:
        for seed in (3, 4, 5):
            sim_game(tmp_path / str(seed), seed, rules=rules)
    finally:
        flow.Game.say_referee = real
    flags = said.count(X.text("NXP-01"))
    results = [t for t in said if t.startswith((" the penalty is accepted", " the penalty is declined")) or " yards, it will be " in t
               or t.strip().startswith("it will be")]
    assert flags > 0 and results, (flags, said[:20])
    for text in said:
        assert "<" not in text, text                                            # every placeholder filled


def test_the_result_texts_name_the_yards_and_the_down():
    assert X.text("NXP-24", yards=10, situation="it will be third and 5 on your 30 yard line") == (
        " the penalty is accepted. 10 yards, it will be third and 5 on your 30 yard line. ")
    assert X.text("NXP-25", situation="it will be second and 10 on your 30 yard line").startswith(" the penalty is declined, ")


# ----- 2: the whistle -----

def test_no_whistle_of_these_rules_is_the_originals_and_the_players_whistle_wav_replaces_them_all(tmp_path, monkeypatch):
    st, calls = stadium_with()
    for _ in range(40):
        assert st.whistle(None) is not None
    for context in ST.CONTEXT_WHISTLES:
        assert os.path.basename(st.whistle(context)).startswith("whistle_")
    mine = tmp_path / "mine"
    mine.mkdir()
    (mine / "whistle.wav").write_bytes(b"x")
    st.folders = (str(mine), ST.shipped_folder())
    for context in list(ST.CONTEXT_WHISTLES) + [None]:
        assert st.whistle(context) == str(mine / "whistle.wav")


# ----- 3: the crowd -----

def test_the_crowd_reactions_have_their_own_channel_and_are_heard_over_the_bed():
    st, calls = stadium_with()
    sounds = st.game.sounds
    st.between(None, facts(O.PASS_COMPLETE, side=1, yards=35))
    st.note_outcome(None, types.SimpleNamespace(kind=O.RUN, yards=9, two_point_try=False))
    assert [name for name, level in calls] == ["crowd_big_play", "hit_pads"]
    assert sounds.slots == [CROWD_SLOT, None]                                  # the hit is on the extra channel (the default), not the crowd's
    for name in ST.ALL_NAMES:
        if name.startswith("crowd_"):
            assert ST.LEVELS[name] >= -1200, name


def test_a_flag_on_the_other_team_is_cheered_and_one_on_yours_is_booed():
    st, calls = stadium_with()
    st.penalty(None, 2)
    st.penalty(None, 1)
    assert [name for name, level in calls] == ["flag_throw", "crowd_flag_cheer", "crowd_boo"]


def test_a_play_a_penalty_or_a_review_took_over_gets_no_crowd_reaction_in_a_real_game(tmp_path):
    seen = []

    class Watching(RecordingRules):
        def after_outcome(self, state, outcome):
            result = super().after_outcome(state, outcome)
            if result.then is not None and self.broadcast.facts is not None:
                seen.append(self.broadcast.facts.taken_over)
            return result

    for seed in (2, 7):
        sim_game(tmp_path / str(seed), seed, rules=Watching(penalties_on=True, challenges_on=True, broadcast_on=True, stadium_on=True))
    assert seen and all(seen)


# ----- 5: the blitz -----

def test_enter_on_the_blitz_item_draws_only_calls_that_send_five_or_more():
    family = [c for c in C.CATALOG if c.side == "D" and c.family == BLITZ_FAMILY]
    assert any(c.params.rushers < 5 for c in family)                          # the four-man looks are in the family's lists
    kept = blitz_family_sends_five(family)
    assert kept and all(c.params.rushers >= 5 for c in kept)
    looks = [c for c in family if c.params.rushers < 5]
    assert blitz_family_sends_five(looks) == looks                               # a list of four-man looks only is left as it is
    other = [c for c in C.CATALOG if c.side == "D" and c.family != BLITZ_FAMILY][:5]
    assert blitz_family_sends_five(other) == other


def test_more_rushers_get_home_more_often():
    for shell in (0, 1):
        rates = [MD.SACK_BY_RUSHERS[n][shell] for n in (4, 5, 6)]
        assert rates == sorted(rates) and rates[1] >= rates[0] * 1.5 and rates[2] >= rates[0] * 2


# ----- 6: the start of a game -----

def test_the_nfl_rules_start_a_game_with_no_jingle_and_no_crowd_surge_and_classic_keeps_them():
    assert NflRules().start_sounds() is False and CLASSIC.start_sounds() is True
