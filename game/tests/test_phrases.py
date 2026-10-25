"""The play-by-play texts and the phrase histories (GAME_SPEC 5.8 to 5.11; Q34, Q35). This is inspired by Jim Kitchen.

Every text of game/phrases.py is a string of the original's exe (spec/strings_all.tsv); the histories keep a phrase from
coming back as the lifted routines do (the snap phrase 0x441271, the hand-off GoSub 0x451b58, the drop-back 0x4528c8).
"""
import pytest

from nfl4.game import phrases as P
from nfl4.game.menus import defense_menu, offense_menu
from nfl4.game.phrases import GroupedPhrases, PhraseHistory
from nfl4.game.rnd import GameRandom
from nfl4.game.setup import RUN_DIRECTIONS, SNAP_WORDS
from randsources import ScriptedRandom, StuckRandom, below_value, value_for
from specfiles import original_strings


def module_texts():
    texts = {}
    for name, value in vars(P).items():
        if name.startswith("_") or name in ("annotations",):
            continue
        if isinstance(value, str):
            texts[name] = [value]
        elif isinstance(value, tuple) and all(isinstance(v, str) for v in value):
            texts[name] = list(value)
        elif isinstance(value, tuple) and all(isinstance(v, tuple) for v in value):
            texts[name] = [v for pair in value for v in pair if isinstance(v, str)]
        elif isinstance(value, dict) and all(isinstance(v, str) for v in value.values()):
            texts[name] = list(value.values())
    return texts


def test_every_text_of_the_play_engine_is_a_string_of_the_original():
    strings = original_strings()
    missing = [(name, text) for name, values in module_texts().items() for text in values if text not in strings]
    assert missing == []
    assert len(module_texts()) > 100


def test_no_name_of_the_phrase_module_is_assigned_twice():
    """A second assignment silently replaces the first (" the " for the toss had replaced " the " for midfield)."""
    import ast
    import collections
    tree = ast.parse(open(P.__file__, encoding="utf-8").read())
    names = collections.Counter(n.id for node in tree.body if isinstance(node, ast.Assign)
                                for target in node.targets for n in ast.walk(target) if isinstance(n, ast.Name))
    assert [name for name, count in names.items() if count > 1] == []
    assert P.THE == " the" and P.THE_TEAM == " the "


def test_the_lists_have_the_original_lengths_and_spellings():
    assert len(P.SNAP_PHRASES) == 13 and len(P.THROW_PHRASES) == 9 and len(P.CATCH_PHRASES) == 9
    assert len(P.HANDOFF_PHRASES) == 9 and len(P.DROPBACK_PHRASES) == 11 and len(P.RETURN_RUNS) == 5
    assert len(P.FG_MISSES) == 6 and len(P.TD_CATCHES) == 3 and len(P.STAT_NAMES) == 11
    assert P.DROPBACK_PHRASES[6] == "drops back  to pass"                 # two spaces, as in the exe
    assert P.READY_TO_KICK_OFF == "  is ready to kick off "
    assert P.SECOND_AIRY.endswith("second airy") and "lookes" in P.RETURN_RUNS[2]
    assert [uses for uses, _ in P.HANDOFF_PHRASES] == [True, True, True, False, True, True, False, False, True]


def test_the_menus_and_word_lists_are_strings_of_the_original():
    strings = original_strings()
    for item in offense_menu() + defense_menu():
        assert item.text in strings
    for word in SNAP_WORDS + RUN_DIRECTIONS:
        assert word in strings
    assert [i.digit for i in offense_menu()] == list(range(1, 9))
    assert [i.action for i in offense_menu(two_point_try=True)] == [("play", n) for n in range(1, 6)]
    assert defense_menu()[-1].action == ("save", 0) and offense_menu()[-1].action == ("save", 0)


# ----- PhraseHistory: the last n values are drawn again -----

def test_a_phrase_history_rejects_its_last_values_and_shifts():
    src = ScriptedRandom([value_for(13, 4), value_for(13, 4), value_for(13, 9)], strict=True)
    rnd = GameRandom(src)
    history = PhraseHistory(6)
    assert history.draw(rnd, 13, "test") == 4
    assert history.draw(rnd, 13, "test") == 9                              # the second 4 was drawn again
    assert history.values == [0, 0, 0, 0, 4, 9] and src.left == 0
    for value in (1, 2, 3, 5, 6):
        history.enter(value)
    assert history.values == [9, 1, 2, 3, 5, 6]                           # the oldest dropped out


def test_a_stuck_source_ends_through_the_bound():
    rnd = GameRandom(StuckRandom(value_for(13, 4)))
    rnd.redraw_limit = 50
    history = PhraseHistory(6)
    history.enter(4)
    assert history.draw(rnd, 13, "test") == 1 and rnd.fallbacks == 1


# ----- the hand-off and the drop-back (5.9, Q34, Q35) -----

def handoff_draw(group, phrase):
    return [below_value(4, group), value_for(9, phrase)]


def test_the_handoffs_first_call_draws_group_0_again_and_then_never_rejects_a_group():
    src = ScriptedRandom([below_value(4, 0)] + handoff_draw(2, 5) + handoff_draw(2, 7), strict=True)
    rnd = GameRandom(src)
    handoff = GroupedPhrases(4, 9, "hand-off")
    assert handoff.draw(rnd, lambda g: " Smith takes the snap") == 5          # value 23, the plain phrase 5 (Q35)
    assert handoff.memory == " Smith takes the snap"                        # the SENTENCE, not the group (Q34)
    assert handoff.draw(rnd, lambda g: " Smith has the ball") == 7           # the same group is not rejected
    assert handoff.history.values[-2:] == [23, 25] and src.left == 0


def test_the_handoff_draws_both_numbers_again_when_the_value_is_in_its_history_of_16():
    src = ScriptedRandom(handoff_draw(1, 1) + handoff_draw(1, 1) + handoff_draw(3, 1), strict=True)
    rnd = GameRandom(src)
    handoff = GroupedPhrases(4, 9, "hand-off")
    assert handoff.draw(rnd, lambda g: "x") == 1
    assert handoff.draw(rnd, lambda g: "x") == 1                            # value 10 again: drawn again, 28
    assert handoff.history.values[-2:] == [10, 28] and src.left == 0


def test_the_dropback_rejects_the_previous_group_and_its_first_call_group_0():
    src = ScriptedRandom([below_value(3, 0), below_value(3, 1), value_for(11, 3),
                          below_value(3, 1), below_value(3, 2), value_for(11, 11)], strict=True)
    rnd = GameRandom(src)
    dropback = GroupedPhrases(3, 11, "drop-back")
    assert dropback.draw(rnd, lambda g: g) == 3 and dropback.memory == 1
    assert dropback.draw(rnd, lambda g: g) == 11 and dropback.memory == 2   # group 1 again was drawn again
    assert dropback.history.values[-2:] == [14, 33] and src.left == 0


def test_over_many_calls_no_value_of_the_last_16_comes_back():
    rnd = GameRandom(__import__("random").Random(4))
    handoff = GroupedPhrases(4, 9, "hand-off")
    values = []
    for _ in range(2000):
        handoff.draw(rnd, lambda g: "sentence")
        values.append(handoff.history.values[-1])
    for i in range(16, len(values)):
        assert values[i] not in values[i - 16:i]
    assert rnd.fallbacks == 0


@pytest.mark.parametrize("memory, group, rejected", [(None, 0, True), (None, 1, False), ("text", 0, False),
                                                     (2, 2, True), (2, 1, False)])
def test_the_group_memory_compares_as_vb_compares_variants(memory, group, rejected):
    phrases = GroupedPhrases(4, 9, "test")
    phrases.memory = memory
    assert phrases._rejects(group) is rejected
