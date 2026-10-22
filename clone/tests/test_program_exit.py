"""The exit on the virtual-clock rig. This is inspired by Jim Kitchen.

GAME_SPEC 3 step 9 and the Exit bullet, G-F6, D-006, D-100, SOUND_DESIGN 4 (CODE (lifted) Form_Load 0x48a054 to 0x48aad2): the
season files go when gtp is 0, foot0 plays and is waited for, the thank-you is spoken (waited), the sounds are released and the
program ends. The original's "game menu not found" branch (two Beeps and "Sorry, but I could not find the Kitchensinc game menu
program.") is not run: the owner's rule 0.26 (S8.2, D-100) says no game says that a menu program is missing.
"""
import pytest

from nfl4.game import texts
from nfl4.game.keys import GameQuit
from programrig import DOWN, ENTER, preset_season, program_rig, said

EXIT = [DOWN, DOWN, DOWN, ENTER]
THANK_YOU = texts.THANK_YOU


def marker(rig, text):
    rig.sapi.events.append(("marker", text))


def test_the_exit_plays_foot0_says_the_thank_you_releases_the_sounds_and_ends(tmp_path):
    rig = program_rig(tmp_path, EXIT, preset=preset_season())
    real = rig.sounds.stop_all
    rig.sounds.stop_all = lambda: (marker(rig, "sounds released"), real())[-1]
    rig.run()
    order = [text for kind, text in rig.sapi.events if kind in ("speak", "marker")]
    assert order[-2:] == [THANK_YOU, "sounds released"]
    plays = [(e.slot, e.sound_id, e.time) for e in rig.slot_log if e.action == "play"]
    exit_foot0 = [p for p in plays if p[1] == "snd_foot0"][-1]                     # play("0", 0), 0x48a54f
    assert exit_foot0[0] == 0


def test_the_exit_has_no_menu_program_sentence_and_no_beep(tmp_path):
    rig = program_rig(tmp_path, EXIT, preset=preset_season()).run()
    assert texts.NO_GAME_MENU_ORIGINAL not in said(rig) and said(rig)[-1] == THANK_YOU
    assert rig.beeper.calls == 0 and not [e for e in rig.slot_log if e.sound_id == "beep_exit"]
    assert not [t for kind, t in rig.sapi.events if kind == "speak" and "game menu" in t.lower()]


def test_no_text_of_the_game_says_that_a_menu_program_is_missing():
    # rule 0.26: the original's sentence stays only under its _ORIGINAL name, never in a text the game can say
    said_texts = {name: value for name, value in vars(texts).items() if isinstance(value, str) and not name.endswith("_ORIGINAL")}
    assert [n for n, v in said_texts.items() if "game menu" in v.lower() and "program" in v.lower()] == []


def test_foot0_is_waited_for_before_the_thank_you_and_the_crowd_beds_play_under_both(tmp_path):
    # Form_Load releases the DirectSound objects only after the thank-you (0x48a5ed): the beds are heard until then
    rig = program_rig(tmp_path, EXIT, preset=preset_season()).run()
    foot0_ends = [e.time for e in rig.slot_log if e.action == "stop" and e.slot == 0 and e.time > rig.slot_log[3].time]
    released = [e.time for e in rig.slot_log if e.action == "stop" and e.slot == 1][-1]
    assert released >= foot0_ends[-1]
    bed_stops = [e for e in rig.slot_log if e.action == "stop" and e.slot in (1, 2)]
    assert len(bed_stops) == 2 and bed_stops[0].time == bed_stops[1].time          # one release for everything


def test_the_whole_exit_takes_foot0_and_the_thank_you_and_nothing_else(tmp_path):
    rig = program_rig(tmp_path, EXIT, preset=preset_season(), speech_per_char=0.01)
    rig.run()
    events = [e for e in rig.slot_log if e.slot == 0 and e.sound_id == "snd_foot0" and e.action == "play"]
    start = events[-1].time                                                        # play("0", 0)
    stop = next(e.time for e in rig.slot_log if e.action == "stop" and e.slot == 0 and e.time > start)
    expected = (stop - start) + len(THANK_YOU) * 0.01
    assert abs((rig.clock.now - start) - expected) < 0.05                          # nothing else takes time


def test_the_thank_you_is_not_cut_by_a_key(tmp_path):
    rig = program_rig(tmp_path, EXIT, preset=preset_season(), speech_per_char=0.2)
    rig.keys.post(65)                                                                # a key typed while it is spoken
    rig.run()
    assert said(rig)[-1] == THANK_YOU


def test_exit_says_the_thank_you_when_there_is_no_sound_layer(tmp_path):
    rig = program_rig(tmp_path, EXIT, preset=preset_season())
    rig.game.sounds = None                                                          # a program without sounds
    rig.run()
    assert said(rig)[-1] == THANK_YOU


def test_the_season_files_are_deleted_first_when_the_season_is_over_at_the_exit(tmp_path):
    rig = program_rig(tmp_path, [], preset=preset_season())
    rig.game.season.gtp = 0
    from nfl4.game.program import Program
    Program(rig.game, rig.store).exit_program()
    assert rig.store.calls == ["delete_season_files"] and rig.store.deleted == 1
    plays = [e.sound_id for e in rig.slot_log if e.action == "play"]
    assert plays[0] == "snd_foot0" and said(rig) == [THANK_YOU]


def test_the_exit_with_a_running_season_deletes_nothing(tmp_path):
    rig = program_rig(tmp_path, EXIT, preset=preset_season()).run()
    assert rig.store.deleted == 0


def test_the_exit_writes_its_log_line(tmp_path, caplog):
    caplog.set_level("INFO", logger="nfl4.game")
    program_rig(tmp_path, EXIT, preset=preset_season()).run()
    assert any("exit: the thank-you is said" in r.getMessage() for r in caplog.records)


def test_closing_the_window_in_the_menu_ends_the_game_with_no_exit_sequence(tmp_path):
    rig = program_rig(tmp_path, [], preset=preset_season())
    rig.keys.close()                                                                # the window's close handler
    with pytest.raises(GameQuit):
        rig.run()
    assert THANK_YOU not in said(rig) and rig.beeper.calls == 0
