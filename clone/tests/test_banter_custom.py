"""The banter with the player's pool: the same draw rule and call order as the original (GAME_SPEC 5.13), custom lines. This is inspired by Jim Kitchen.

D-035, D-048, CUSTOMIZABLE_CONTENT 12. What was written down before the code, from the lifted GoSub 0x45915e: after the line
and the name are drawn and rady has paused, the alternatives are drawn, then clk, the first text (waited), foot13 after it as many
times as the line says, clk, the second text when there is one, clk; so an original line gives exactly three clk calls
(before, after the first group, after the second group even when there is none) and the sounds' own clk inside each play. A
player's line keeps that shape: a group is a spoken part with the sounds and pauses after it, and clk follows each group (and a
line of one group has the second clk too). The pool's size takes the place of 142 and the lines are told apart by number.
"""
import os
import random

import pytest

from gamerig import Rig
from nfl4.data.customlists import Problems
from nfl4.game.banter import line_texts, speak_banter
from nfl4.game.banter_lines import LINES
from nfl4.game.banter_pool import DEFAULT_LINES, build_pool
from nfl4.game.gamestate import GameState
from nfl4.audio.library import SOUND_FILE_NOTICE
from randsources import ScriptedRandom, below_value, value_for
from wavmaker import sine, write

NAMES = ["N%d" % i for i in range(1, 59)]


def make_rig(tmp_path, values=None, seed=None, pool=None, comments_off=False, sound_level=0):
    rng = ScriptedRandom(values, strict=True) if values is not None else random.Random(seed or 1)
    rig = Rig(sounds_dir=tmp_path / "sounds", rng=rng, sound_level=sound_level)
    rig.rnd.trace = []
    rig.game.comtog_source = lambda: 1 if comments_off else 0
    folder = tmp_path / "customize" / "sounds"
    os.makedirs(folder, exist_ok=True)
    rig.game.banter_sounds_dir = str(folder)
    if pool is not None:
        rig.game.banter_pool = pool
    state = GameState()
    state.banter_names = list(NAMES)
    state.quarterbacks = {1: "Starr", 2: "Unitas"}
    return rig, state


def pool_of(overrides):
    problems = Problems("banter.txt")
    pool = build_pool(overrides, problems)
    assert problems.count == 0, problems.messages
    return pool


def record(rig):
    """Everything the line does, in order: clk, say (with its rate step), the bleep, a player's file."""
    events = []
    clk, say, play, play_file = rig.keys.clk, rig.game.say, rig.sounds.play, rig.sounds.play_file

    def clk_(): events.append("clk"); return clk()
    def say_(text, rate_step=0): events.append(("say", text, rate_step)); return say(text, rate_step=rate_step)
    def play_(n, v): events.append(("play", n)); return play(n, v)
    def play_file_(path, limit=None): events.append(("file", os.path.basename(path))); return play_file(path, limit=limit)

    rig.keys.clk, rig.game.say, rig.sounds.play, rig.sounds.play_file = clk_, say_, play_, play_file_
    return events


def one_line(rig, state, number, name_index=7, extra=()):
    """Script the draws of one call that picks pool line `number` (its place in the pool is found from the pool)."""
    lines = rig.game.banter_pool.lines
    place = [line.number for line in lines].index(number) + 1
    rig.rnd.source.values[:] = [value_for(len(lines), place), value_for(58, name_index), below_value(30, 0)] + list(extra)


# ----- the original lines, all 142: the same speech, sounds, draws and clk calls as before -----

@pytest.mark.parametrize("line", LINES, ids=lambda line: "B%03d" % line.number)
def test_an_original_line_speaks_plays_and_clears_the_key_exactly_as_the_lifted_routine_does(tmp_path, line):
    rig, state = make_rig(tmp_path, [])
    events = record(rig)
    extra = [value_for(len(line.alternatives), 2)] if line.alternatives else []
    one_line(rig, state, line.number, extra=extra)
    speak_banter(rig.game, state)
    first, second = line_texts(line, "N7", "Unitas", 2 if line.alternatives else None)
    expected = ["clk", ("say", first, line.rate_step)]
    expected += [("play", 13), "clk"] * line.bleeps
    expected += ["clk"] + ([("say", second, 0)] if second != "" else []) + ["clk"]
    assert events == expected
    assert rig.rnd.trace == [142, 58, 30] + ([len(line.alternatives)] if line.alternatives else [])
    assert state.banter_used == [line.number] and rig.rnd.source.left == 0
    assert len([e for e in rig.slot_log if e.action == "play"]) == line.bleeps


def test_the_default_pool_is_the_builtin_lines_themselves(tmp_path):
    rig, state = make_rig(tmp_path, [])
    assert rig.game.banter_pool.lines == DEFAULT_LINES and rig.game.banter_pool.size == 142


# ----- a player's lines -----

def test_a_text_line_inserts_the_name_and_the_opponents_quarterback(tmp_path):
    pool = pool_of({n: None for n in range(1, 143)} | {143: "[name] met [opponent quarterback] at the game"})
    rig, state = make_rig(tmp_path, [], pool=pool)
    events = record(rig)
    one_line(rig, state, 143, name_index=9)
    speak_banter(rig.game, state)
    assert events == ["clk", ("say", "N9 met Unitas at the game", 0), "clk", "clk"]
    assert rig.rnd.trace == [1, 58, 30]


def test_a_sound_line_plays_the_players_file_at_the_sound_volume_and_waits_for_its_end(tmp_path):
    pool = pool_of({n: None for n in range(1, 143)} | {150: "[sound boo.wav]"})
    rig, state = make_rig(tmp_path, [], pool=pool, sound_level=-500)
    write(tmp_path / "customize" / "sounds" / "boo.wav", sine(440, 0.4, 11025), rate=11025)
    events = record(rig)
    one_line(rig, state, 150)
    before = rig.clock()
    speak_banter(rig.game, state)
    waited = rig.clock() - before
    assert events == ["clk", ("file", "boo.wav"), "clk", "clk", "clk"]
    assert 0.4 <= waited < 0.5
    played = [e for e in rig.slot_log if e.action == "play"]
    assert len(played) == 1 and played[0].sound_id == "file boo.wav" and played[0].source == "player"
    assert played[0].volume == -500 and rig.said == []                      # nothing is spoken for a sound-only line


def test_text_then_sound_then_text_are_said_and_played_in_that_order(tmp_path):
    pool = pool_of({n: None for n in range(1, 143)} | {151: "what a hit! [sound crunch.wav] Ghip, did you see that?"})
    rig, state = make_rig(tmp_path, [], pool=pool)
    write(tmp_path / "customize" / "sounds" / "crunch.wav", sine(300, 0.2, 11025), rate=11025)
    events = record(rig)
    one_line(rig, state, 151)
    speak_banter(rig.game, state)
    assert events == ["clk", ("say", "what a hit!", 0), ("file", "crunch.wav"), "clk", "clk",
                      ("say", "Ghip, did you see that?", 0), "clk"]


def test_the_bleep_then_and_faster_follow_the_originals_shape(tmp_path):
    pool = pool_of({n: None for n in range(1, 143)} | {143: "holy [bleep] [bleep] Ghip [then] oh well [faster] quick"})
    rig, state = make_rig(tmp_path, [], pool=pool)
    events = record(rig)
    one_line(rig, state, 143)
    speak_banter(rig.game, state)
    assert events == ["clk", ("say", "holy", 0), ("play", 13), "clk", ("play", 13), "clk", "clk", ("say", "Ghip", 0), "clk",
                      ("say", "oh well", 0), "clk", ("say", "quick", 1), "clk"]


def test_a_choice_is_drawn_after_the_pause_in_line_order_with_equal_chances(tmp_path):
    pool = pool_of({n: None for n in range(1, 143)} | {143: "a [one of: x | y | z] b [then] [one of: p | q]"})
    rig, state = make_rig(tmp_path, [], pool=pool)
    one_line(rig, state, 143, extra=[value_for(3, 3), value_for(2, 1)])
    speak_banter(rig.game, state)
    assert rig.rnd.trace == [1, 58, 30, 3, 2]
    assert [t for t, _, _ in rig.said] == ["a z b", "p"]


def test_pause_is_rady_and_pause_two_is_two_seconds(tmp_path):
    pool = pool_of({n: None for n in range(1, 143)} | {143: "a [pause] b", 144: "[pause 2]"})
    rig, state = make_rig(tmp_path, [], pool=pool)
    one_line(rig, state, 143, extra=[below_value(30, 0)])
    speak_banter(rig.game, state)
    assert rig.rnd.trace == [2, 58, 30, 30] and [t for t, _, _ in rig.said] == ["a", "b"]
    one_line(rig, state, 144)
    before = rig.clock()
    speak_banter(rig.game, state)
    assert 2.0 <= rig.clock() - before < 2.1 and rig.rnd.trace[-3:] == [2, 58, 30]


@pytest.mark.parametrize("what", ["missing", "empty", "garbage"])
def test_a_sound_file_that_cannot_be_used_is_skipped_the_rest_is_said_and_one_notice_is_spoken(tmp_path, what):
    pool = pool_of({n: None for n in range(1, 143)} | {143: "before [sound bad.wav] after"})
    rig, state = make_rig(tmp_path, [], pool=pool)
    path = tmp_path / "customize" / "sounds" / "bad.wav"
    if what == "empty":
        path.write_bytes(b"")
    elif what == "garbage":
        path.write_bytes(bytes(random.Random(3).randrange(256) for _ in range(500)))
    events = record(rig)
    for _ in range(2):
        state.banter_used = []
        one_line(rig, state, 143)
        speak_banter(rig.game, state)
    assert [e for e in events if isinstance(e, tuple) and e[0] == "say"] == [("say", "before", 0), ("say", "after", 0)] * 2
    assert not [e for e in rig.slot_log if e.action == "play" and e.source == "player"]
    assert rig.audio.library.take_notices() == [SOUND_FILE_NOTICE]                  # once per start, not per play


def test_a_line_that_names_a_sound_when_there_is_no_folder_still_says_its_text(tmp_path):
    pool = pool_of({n: None for n in range(1, 143)} | {143: "a [sound x.wav] b"})
    rig, state = make_rig(tmp_path, [], pool=pool)
    rig.game.banter_sounds_dir = None
    one_line(rig, state, 143)
    speak_banter(rig.game, state)
    assert [t for t, _, _ in rig.said] == ["a", "b"]


# ----- the pool and the draw rule -----

def test_a_line_switched_off_is_never_drawn_and_every_other_line_comes_once_then_nothing(tmp_path):
    pool = pool_of({45: None, 46: None})
    rig, state = make_rig(tmp_path, seed=9, pool=pool)
    for _ in range(140):
        speak_banter(rig.game, state)
    assert sorted(state.banter_used) == [n for n in range(1, 143) if n not in (45, 46)]
    said_before = len(rig.said)
    speak_banter(rig.game, state)                                        # every line of the pool was used: nothing more
    assert len(rig.said) == said_before and rig.rnd.fallbacks == 0
    spoken = " ".join(t for t, _, _ in rig.said)
    assert "dog bone" not in spoken and "thirty five years old" not in spoken       # the texts of lines 45 and 46


def test_an_added_line_joins_the_draw_and_the_pool_size_is_the_size_of_the_draw(tmp_path):
    pool = pool_of({143: "my own line", 144: "another of mine"})
    rig, state = make_rig(tmp_path, [], pool=pool)
    one_line(rig, state, 144)
    speak_banter(rig.game, state)
    assert rig.rnd.trace == [144, 58, 30] and rig.said[0][0] == "another of mine" and state.banter_used == [144]


def test_a_used_line_is_drawn_again_by_its_number_in_a_changed_pool(tmp_path):
    pool = pool_of({n: None for n in range(1, 143)} | {200: "a", 201: "b", 202: "c"})
    rig, state = make_rig(tmp_path, [value_for(3, 2), value_for(3, 3), value_for(58, 1), below_value(30, 0)], pool=pool)
    state.banter_used = [201, 1]                                          # one used before the file was reloaded, one not in the pool
    speak_banter(rig.game, state)
    assert rig.rnd.trace == [3, 3, 58, 30] and rig.said[0][0] == "c" and state.banter_used == [201, 1, 202]


def test_a_pool_with_no_line_on_is_silent_like_comments_off(tmp_path):
    rig, state = make_rig(tmp_path, [], pool=pool_of({n: None for n in range(1, 143)}))
    events = record(rig)
    speak_banter(rig.game, state)
    assert events == [] and rig.rnd.trace == [] and rig.said == [] and state.banter_used == []


def test_comments_off_silences_the_players_lines_and_sounds_too(tmp_path):
    pool = pool_of({143: "mine", 144: "[sound x.wav]"})
    rig, state = make_rig(tmp_path, [], pool=pool, comments_off=True)
    events = record(rig)
    speak_banter(rig.game, state)
    assert events == [] and rig.rnd.trace == [] and rig.said == [] and rig.slot_log == []


def test_a_pool_of_one_and_a_pool_of_five_hundred_never_repeat_a_line_in_a_game(tmp_path):
    one = pool_of({n: None for n in range(1, 143)} | {143: "only"})
    rig, state = make_rig(tmp_path, seed=2, pool=one)
    speak_banter(rig.game, state)
    speak_banter(rig.game, state)
    assert [t for t, _, _ in rig.said] == ["only"] and state.banter_used == [143]
    big = pool_of({n: None for n in range(1, 143)} | {n: "line %d" % n for n in range(143, 643)})
    rig, state = make_rig(tmp_path, seed=3, pool=big)
    for _ in range(500):
        speak_banter(rig.game, state)
    assert sorted(state.banter_used) == list(range(143, 643)) and len({t for t, _, _ in rig.said}) == 500
    assert rig.rnd.fallbacks == 0
