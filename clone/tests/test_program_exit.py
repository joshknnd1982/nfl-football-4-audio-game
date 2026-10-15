"""The exit on the virtual-clock rig. This is inspired by Jim Kitchen.

GAME_SPEC 3 step 9 and the Exit bullet, G-F6, D-006, SOUND_DESIGN 4, B-X13 (CODE (lifted) Form_Load 0x48a054 to 0x48aad2): the
season files go when gtp is 0, foot0 plays and is waited for, the thank-you is spoken (waited), the sounds are released, then
the original's "game menu not found" branch: Beep, 0.1 s, Beep, 0.1 s, the sentence, 0.2 s, the end.
"""
import pytest

from nfl4.game import help_texts as H
from nfl4.game import texts
from nfl4.game.keys import GameQuit
from programrig import DOWN, ENTER, preset_season, program_rig, said

EXIT = [DOWN, DOWN, DOWN, ENTER]
THANK_YOU = texts.THANK_YOU
MENU_LESS = texts.NO_GAME_MENU


def marker(rig, text):
    rig.sapi.events.append(("marker", text))


def test_the_exit_plays_foot0_says_the_thank_you_then_beeps_twice_and_says_the_closing_sentence(tmp_path):
    rig = program_rig(tmp_path, EXIT, preset=preset_season())
    real = rig.sounds.stop_all
    rig.sounds.stop_all = lambda: (marker(rig, "sounds released"), real())[-1]
    rig.run()
    order = [text for kind, text in rig.sapi.events if kind in ("speak", "marker")]
    assert order[-3:] == [THANK_YOU, "sounds released", MENU_LESS]
    plays = [(e.slot, e.sound_id, e.time) for e in rig.slot_log if e.action == "play"]
    exit_foot0 = [p for p in plays if p[1] == "snd_foot0"][-1]                     # play("0", 0), 0x48a54f
    beeps = [p for p in plays if p[1] == "beep_exit"]
    assert exit_foot0[0] == 0 and [b[0] for b in beeps] == [7, 7] and rig.beeper.calls == 2
    assert 0.1 <= beeps[1][2] - beeps[0][2] < 0.11                                  # dy(0.1) between the two Beeps
    assert beeps[0][2] > exit_foot0[2]                                              # after foot0 and the thank-you


def test_foot0_is_waited_for_before_the_thank_you_and_the_crowd_beds_play_under_both(tmp_path):
    # Form_Load releases the DirectSound objects only after the thank-you (0x48a5ed): the beds are heard until then
    rig = program_rig(tmp_path, EXIT, preset=preset_season()).run()
    foot0_ends = [e.time for e in rig.slot_log if e.action == "stop" and e.slot == 0 and e.time > rig.slot_log[3].time]
    released = [e.time for e in rig.slot_log if e.action == "stop" and e.slot == 1][-1]
    beep = [e.time for e in rig.slot_log if e.sound_id == "beep_exit"][0]
    assert released <= beep and released >= foot0_ends[-1]
    bed_stops = [e for e in rig.slot_log if e.action == "stop" and e.slot in (1, 2)]
    assert len(bed_stops) == 2 and bed_stops[0].time == bed_stops[1].time          # one release for everything


def test_the_whole_exit_takes_foot0_the_thank_you_the_beeps_the_sentence_and_the_two_pauses(tmp_path):
    rig = program_rig(tmp_path, EXIT, preset=preset_season(), speech_per_char=0.01)
    rig.run()
    events = [e for e in rig.slot_log if e.slot == 0 and e.sound_id == "snd_foot0" and e.action == "play"]
    start = events[-1].time                                                        # play("0", 0)
    stop = next(e.time for e in rig.slot_log if e.action == "stop" and e.slot == 0 and e.time > start)
    expected = (stop - start) + (len(THANK_YOU) + len(MENU_LESS)) * 0.01 + 0.1 + 0.1 + 0.2
    assert abs((rig.clock.now - start) - expected) < 0.05                          # nothing else takes time


def test_a_key_cuts_the_closing_sentence_and_ends_the_program_at_once(tmp_path):
    rig = program_rig(tmp_path, EXIT + [("cut", 0.5, "x")], preset=preset_season(), speech_per_char=0.2)
    rig.run()
    closing = len(MENU_LESS) * 0.2                                                  # 12.4 s if it were spoken to the end
    beeps = [e.time for e in rig.slot_log if e.sound_id == "beep_exit"]
    assert rig.clock.now - beeps[1] < closing / 4 and rig.keys.answers == []        # cut about 0.5 s in, then dy(0.2)


def test_no_hot_key_menu_opens_in_the_closing_sentence(tmp_path):
    rig = program_rig(tmp_path, EXIT + [("cut", 0.5, 116)], preset=preset_season(), speech_per_char=0.05)
    rig.run()
    assert H.SPECIAL_KEYS not in said(rig)                                          # F5 only ends the sentence
    assert said(rig)[-1] == MENU_LESS


def test_the_thank_you_is_not_cut_by_a_key(tmp_path):
    rig = program_rig(tmp_path, EXIT, preset=preset_season(), speech_per_char=0.2)
    rig.keys.post(65)                                                                # a key typed while it is spoken
    rig.run()
    assert said(rig)[-2:] == [THANK_YOU, MENU_LESS]


def test_exit_beeps_use_the_sound_chain_and_say_nothing_when_there_is_no_sound_layer(tmp_path):
    rig = program_rig(tmp_path, EXIT, preset=preset_season())
    rig.game.sounds = None                                                          # a program without sounds
    rig.run()
    assert said(rig)[-2:] == [THANK_YOU, MENU_LESS]


def test_the_season_files_are_deleted_first_when_the_season_is_over_at_the_exit(tmp_path):
    rig = program_rig(tmp_path, [], preset=preset_season())
    rig.game.season.gtp = 0
    from nfl4.game.program import Program
    Program(rig.game, rig.store).exit_program()
    assert rig.store.calls == ["delete_season_files"] and rig.store.deleted == 1
    plays = [e.sound_id for e in rig.slot_log if e.action == "play"]
    assert plays[0] == "snd_foot0" and said(rig) == [THANK_YOU, MENU_LESS]


def test_the_exit_with_a_running_season_deletes_nothing(tmp_path):
    rig = program_rig(tmp_path, EXIT, preset=preset_season()).run()
    assert rig.store.deleted == 0


def test_closing_the_window_in_the_menu_ends_the_game_with_no_exit_sequence(tmp_path):
    rig = program_rig(tmp_path, [], preset=preset_season())
    rig.keys.close()                                                                # the window's close handler
    with pytest.raises(GameQuit):
        rig.run()
    assert THANK_YOU not in said(rig) and rig.beeper.calls == 0
