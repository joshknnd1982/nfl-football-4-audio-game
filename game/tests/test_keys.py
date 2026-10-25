"""The original's key fields and waits, with typed characters (nfl4 S7.1). This is inspired by Jim Kitchen.

GAME_SPEC 8.1 (g = the key code text, g2 = LCase(Chr(code)), clk, getkey, dy), GAP_REGISTER G-K1 and G-K5, B-W3.
"""
import threading
import time

import pytest

from gamerig import Clock, ScriptedKeys
from nfl4.game.keys import GameQuit, KeyInput, key_char
from nfl4.speech.fake import FakeBackend


def test_a_key_and_the_character_it_typed_are_pumped_together_and_g2_stays_the_originals():
    keys = KeyInput()
    keys.post(65)
    keys.post_char("A")                      # Shift+a on the player's keyboard
    keys.pump()
    assert (keys.code_text, keys.char, keys.typed) == ("65", "a", "A")
    keys.post(38)                            # Up types nothing
    keys.pump()
    assert (keys.code_text, keys.char, keys.typed) == ("38", "&", "")


def test_key_char_is_the_originals_lcase_chr_of_the_code():
    assert [key_char(c) for c in (65, 49, 32, 38, 40, 97, 105, 112, 120, 186)] == \
           ["a", "1", " ", "&", "(", "a", "i", "p", "x", "º"]


def test_take_typed_waits_for_the_character_that_follows_its_key():
    keys = KeyInput()
    keys.post(74)
    threading.Timer(0.02, lambda: keys.post_char("j")).start()
    assert keys.read_key() == 74
    assert keys.take_typed(0.5) == "j"


def test_take_typed_never_eats_the_next_key():
    keys = KeyInput()
    keys.post(13)
    keys.post(74)
    keys.post_char("j")
    assert keys.read_key() == 13 and keys.take_typed(0.01) == ""          # Enter typed nothing
    assert keys.read_key() == 74 and keys.take_typed(0.01) == "j"


def test_read_key_skips_modifiers_and_keeps_every_key_typed_ahead():
    keys = KeyInput()
    for code in (16, 17, 65, 18, 66, 13):
        keys.post(code)
    assert [keys.read_key() for _ in range(3)] == [65, 66, 13]


def test_keys_typed_during_a_synchronous_line_only_the_last_survives_with_its_code():
    keys = KeyInput()
    for code in (65, 66, 13):                 # three keys while the game was inside a synchronous say
        keys.post(code)
    keys.clk()                                # the first DoEvents delivers all three; clk clears g2 after it
    assert keys.code_text == "13" and keys.char == ""


def test_dy_waits_its_seconds_pumps_keys_and_is_not_ended_by_one():
    clock = Clock()
    keys = KeyInput(clock=clock, sleep=clock.sleep)
    keys.post(65)
    keys.dy(0.7)
    assert 0.7 < clock.now - 1000.0 < 0.71 and keys.code_text == "65"


def test_getkey_waits_for_a_key_and_stops_speech():
    clock = Clock()
    keys = ScriptedKeys(clock, [("wait", 2.0), 40])
    speech = FakeBackend(clock=clock, sleep=clock.sleep)
    keys.getkey(speech)
    assert keys.code_text == "40" and clock.now - 1000.0 >= 2.0
    assert speech.events[-1] == ("stop", "")


def test_scripted_typing_posts_the_key_and_its_character():
    clock = Clock()
    keys = ScriptedKeys(clock, ["J", "o"])
    keys.getkey(FakeBackend())
    assert (keys.code_text, keys.char, keys.typed) == ("74", "j", "J")
    keys.getkey(FakeBackend())
    assert (keys.code_text, keys.char, keys.typed) == ("79", "o", "o")


def test_a_closed_window_ends_every_wait():
    keys = KeyInput()
    keys.close()
    with pytest.raises(GameQuit):
        keys.pump()
    with pytest.raises(GameQuit):
        keys.read_key()


def test_a_wait_that_never_gets_its_key_fails_the_test_instead_of_hanging():
    keys = ScriptedKeys(Clock(), [])
    t0 = time.monotonic()
    with pytest.raises(AssertionError):
        keys.getkey(FakeBackend())
    assert time.monotonic() - t0 < 10
