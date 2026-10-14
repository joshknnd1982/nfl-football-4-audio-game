"""The S7.1 skeleton on the virtual-clock rig: the spoken title, the notices, the key wait. This is inspired by Jim Kitchen.

Rule 0.5.1 and GAP_REGISTER G-F1 (the title once per launch, by the announcer, waited for), G-K1 (keys typed during a
synchronous line), G-S1 (the barrier). S7.4 replaces the skeleton's key wait with the week loop and the main menu.
"""
import logging

import pytest

from gamerig import Rig
from nfl4.game import texts
from nfl4.game.keys import GameQuit
from nfl4.speech.roles import ANNOUNCER

ESC, A_KEY, ENTER = 27, 65, 13


class Notices:
    def __init__(self, *notices):
        self.notices = list(notices)

    def take_notices(self):
        taken, self.notices = self.notices, []
        return taken


def test_the_title_is_the_first_thing_said_by_the_announcer_and_waited_for():
    rig = Rig([ESC], speech_per_char=0.01).run()
    assert rig.said == [(texts.TITLE_SPOKEN, ANNOUNCER, 0)]
    assert texts.TITLE_SPOKEN == " NFL Football 4 by Josh Kennedy, inspired by Jim Kitchen "   # rule 0.5.1
    kinds = [kind for kind, _ in rig.sapi.events]
    assert kinds[:2] == ["speak", "wait"]                                   # synchronous: a barrier
    assert rig.clock.now - 1000.0 >= len(texts.TITLE_SPOKEN) * 0.01 - 1e-9   # the game waited for it to end
    assert rig.keys.waits == 1                                              # then one key wait, ended by Escape


def test_notices_follow_the_title_once_each_and_a_broken_source_is_only_logged(caplog):
    class Broken:
        def take_notices(self):
            raise RuntimeError("settings file gone")

    store = Notices("1 problem found in settings.txt, details are in the log.")
    rig = Rig([ESC], notice_sources=(store, Broken())).run()
    assert [text for text, _, _ in rig.said] == [texts.TITLE_SPOKEN,
                                                "1 problem found in settings.txt, details are in the log."]
    assert any("notices of Broken failed" in r.message for r in caplog.records)


def test_other_keys_do_not_end_the_skeleton_and_each_stops_the_speech():
    rig = Rig([A_KEY, ENTER, "j", ESC]).run()
    assert rig.keys.waits == 4
    assert sum(1 for kind, _ in rig.sapi.events if kind == "stop") == 4      # getkey stops speech after every key


def test_a_key_typed_during_the_title_acts_at_the_first_wait_with_its_code_only():
    # G-K1 (TESTED in S4.3): a synchronous line lets no key through; the next pump delivers them in order, each
    # overwriting the last, and clk then clears the character: the wait ends at once with the last key's code.
    rig = Rig([], speech_per_char=0.01)
    rig.keys.post(A_KEY)
    rig.keys.post(ESC)
    rig.run()
    assert rig.keys.waits == 1 and rig.keys.code_text == str(ESC) and rig.keys.char == ""


def test_closing_the_window_during_the_title_unwinds_the_game():
    rig = Rig([], speech_per_char=0.5)
    rig.keys.close()                                       # the window's close handler
    with pytest.raises(GameQuit):
        rig.run()
    assert rig.clock.now - 1000.0 < 1.0                    # the title's wait was cut, not spoken to its end


def test_with_nvda_mode_the_title_goes_to_nvda_without_a_speaker():
    rig = Rig([ESC], mode="nvda", nvda_running=True).run()
    assert rig.nvda.said == [(texts.TITLE_SPOKEN, None, 0)] and rig.said == []


def test_escape_ends_the_skeleton_and_says_so_in_the_log(caplog):
    caplog.set_level(logging.INFO, logger="nfl4.game")
    Rig([ESC]).run()
    assert any("Escape ends the program" in r.message for r in caplog.records)
