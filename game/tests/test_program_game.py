"""Choice 1 and what follows a game on the virtual-clock rig: the game, the season engine, the standings and their one key, the
crowd beds, a saved game, the end of a season. This is inspired by Jim Kitchen.

GAME_SPEC 3 step 8, G-F2, G-F3, G-A5, B-A12, Q53, D-024 (CODE (lifted) Form_Load 0x489d96 to 0x48a042, 0x48a054 to 0x48a517). pag
is a stand-in whose outcome the test scripts (tests/programrig.py), pog is a stand-in that moves the week on: both have their
own tests (test_pag_*.py, test_season_*.py); here the order of the calls, the speech and the keys between them are the
subject. The expected lists were written from the lifted lines.
"""
from nfl4.game import program_texts as P
from nfl4.game import texts
from nfl4.game import prompt_texts as T
from nfl4.game.playoffs import TeamRef
from programrig import DOWN, ENTER, F1, Outcome, played, preset_season, program_rig, said, saved_game

EXIT = [DOWN, DOWN, DOWN, ENTER]
WEEK = " This is week  %d of Josh Kennedy's N. F. L. football "
THANK_YOU = texts.THANK_YOU
COACH_AND_TEAM = ["k", "i", "m", ENTER, ENTER, ENTER, ENTER]          # kim, yes; the first team, yes
HEADING = " Standings after week number %d"


def marker(rig, text):
    rig.sapi.events.append(("marker", text))


def beds(rig):
    """The sounds' start_crowds and stop_crowds leave a note in the speech events."""
    real_start, real_stop = rig.sounds.start_crowds, rig.sounds.stop_crowds
    rig.sounds.start_crowds = lambda: (marker(rig, "beds start"), real_start())[-1]
    rig.sounds.stop_crowds = lambda: (marker(rig, "beds stop"), real_stop())[-1]


def spoken_or_marked(rig):
    return [text for kind, text in rig.sapi.events if kind in ("speak", "marker")]


# ----- the game (0x489d96 to 0x489ddb) -----

def test_choice_1_plays_the_game_with_the_players_names_and_no_saved_game(tmp_path):
    rig = program_rig(tmp_path, [ENTER, ENTER] + EXIT, preset=preset_season(), outcomes=[played(24, 17)])
    rig.store.names = "the roster of footplay.txt"
    rig.run()
    assert len(rig.plays) == 1
    assert rig.plays[0]["own_names"] == "the roster of footplay.txt" and rig.plays[0]["saved"] is None
    assert rig.plays[0]["save_sink"] == rig.store.save_game


def test_after_the_game_the_season_engine_gets_its_score_then_the_standings_follow(tmp_path):
    rig = program_rig(tmp_path, [ENTER, ENTER] + EXIT, preset=preset_season(), outcomes=[played(24, 17)]).run()
    assert rig.pog_calls == [(24, 17)] and rig.game.ptf == 0
    spoken = said(rig)
    assert spoken.count(HEADING % 1) == 1                           # " Standings after week number 1": gtp is now 2
    assert spoken.index(HEADING % 1) < spoken.index(WEEK % 2)
    assert spoken.count(WEEK % 1) == 1 and spoken.count(WEEK % 2) == 1


def test_the_standings_wait_for_one_key_and_f1_says_them_again(tmp_path):
    # SayStand, then (the voice is done and no key came) a getkey: F1 repeats, any other key ends it (0x489ec5 to 0x48a012)
    rig = program_rig(tmp_path, [ENTER, F1, "x"] + EXIT, preset=preset_season(), outcomes=[played()]).run()
    assert said(rig).count(HEADING % 1) == 2 and rig.keys.answers == []


def test_a_key_typed_while_the_standings_are_spoken_ends_them_and_asks_for_no_second_key(tmp_path):
    rig = program_rig(tmp_path, [ENTER, ("cut", 0.05, "x")] + EXIT, preset=preset_season(), outcomes=[played()],
                      speech_per_char=0.001).run()
    spoken = said(rig)
    assert spoken.count(HEADING % 1) == 1 and rig.keys.answers == []
    assert spoken.index(HEADING % 1) < spoken.index(WEEK % 2)       # the cut standings were followed by week 2, no key wait
    # getkeys: the menu once, then week 2's four, no key wait for the standings; the speech waits: the standings only (the
    # exit's closing sentence is gone, D-100, rule 0.26)
    assert rig.keys.waits == 1 + 4 and rig.keys.speech_waits == 1


def test_silent_standings_after_week_16_wait_for_no_key_q53_not_reproduced(tmp_path):
    def to_the_playoffs(rig):
        rig.game.season.gtp = 18                                    # pog left the player in the play-offs, two rounds on
        rig.game.season.playoffs.pairings = [(TeamRef(1, 1), TeamRef(3, 2))]
    rig = program_rig(tmp_path, [ENTER] + EXIT, preset=preset_season(gtp=16), outcomes=[played()], pog=to_the_playoffs)
    rig.run()
    spoken = said(rig)
    assert not any(t.startswith(" Standings after") for t in spoken)
    assert rig.keys.answers == []
    assert " This is the " in spoken and " division play off week of Josh Kennedy's N. F. L. football " in spoken


def test_the_crowd_beds_restart_when_the_week_loop_begins_again_g_a5(tmp_path):
    rig = program_rig(tmp_path, [ENTER, ENTER] + EXIT, preset=preset_season(), outcomes=[played()])
    beds(rig)
    rig.run()
    order = spoken_or_marked(rig)
    assert order.count("beds start") == 2                              # the start of the program, and week 2
    stop = order.index("beds stop")
    start = order.index("beds start", stop)
    assert stop < order.index(HEADING % 1) < start < order.index(WEEK % 2)    # silent under the results, back before week 2
    plays = [(e.slot, e.volume, e.loop) for e in rig.slot_log if e.action == "play" and e.sound_id in ("snd_foot1", "snd_foot2")]
    assert plays == [(1, -1200, True), (2, -1200, True)] * 2          # at the start of the program, and again for week 2
    assert rig.sounds.crwd1 == -1200                                  # 0x489e52


def test_the_beds_are_not_started_again_when_no_game_stopped_them(tmp_path):
    rig = program_rig(tmp_path, [DOWN, ENTER, DOWN, ENTER] + EXIT, preset=preset_season(gtp=2)).run()
    plays = [e for e in rig.slot_log if e.action == "play" and e.sound_id == "snd_foot1"]
    assert len(plays) == 1                                            # a schedule and a standings view do not touch the beds


def test_the_play_loop_goes_on_to_week_two_with_the_menu_and_a_second_game(tmp_path):
    rig = program_rig(tmp_path, [ENTER, ENTER, ENTER, ENTER] + EXIT, preset=preset_season(),
                      outcomes=[played(10, 3), played(0, 7)]).run()
    assert [p["saved"] for p in rig.plays] == [None, None] and rig.pog_calls == [(10, 3), (0, 7)]
    assert rig.game.season.gtp == 3


# ----- Save Game (0x489e2c) -----

def test_save_game_ends_the_program_with_no_season_engine_and_no_standings(tmp_path):
    rig = program_rig(tmp_path, [ENTER], preset=preset_season(), outcomes=[saved_game()])
    beds(rig)
    rig.run()
    assert rig.pog_calls == [] and rig.game.season.gtp == 1
    spoken = said(rig)
    assert not any(t.startswith(" Standings after") for t in spoken) and spoken[-1] == THANK_YOU
    assert "beds stop" not in spoken_or_marked(rig)                  # pag does not stop the beds on Save Game: the exit does
    assert rig.game.program.ending == "saved"


def test_a_saved_game_skips_the_menu_and_loads_the_game(tmp_path):
    rig = program_rig(tmp_path, [], preset=preset_season(), outcomes=[saved_game()])
    record = rig.store.saved = object()
    rig.run()
    spoken = said(rig)
    assert SELECT_LINE(rig) not in spoken and " 1. play game " not in spoken
    assert rig.plays[0]["saved"] is record and rig.store.saved is record    # SX.14 (NX-S3): the original deleted it as it loaded it; the game keeps it
    assert spoken[1].startswith(" This is week") and spoken[3].startswith(" Today's game is")


def SELECT_LINE(rig):
    return " " + rig.game.season.coach + " select "


def test_after_a_loaded_game_is_played_out_the_menu_is_back(tmp_path):
    rig = program_rig(tmp_path, [ENTER] + EXIT, preset=preset_season(), outcomes=[played()])
    rig.store.saved = object()
    rig.run()
    spoken = said(rig)
    assert spoken.count(SELECT_LINE(rig)) == 1                       # only the second week has a menu
    assert rig.keys.answers == []


# ----- the end of a season (G-F3) -----

def test_a_super_bowl_game_ends_the_season_without_the_engine_or_standings(tmp_path):
    rig = program_rig(tmp_path, [ENTER] + COACH_AND_TEAM + EXIT, preset=preset_season(gtp=20),
                      outcomes=[Outcome(played().result, gtp=0)])
    rig.run()
    assert rig.pog_calls == []                                        # pag set gtp to 0: pog is skipped (0x489e7f)
    assert not any(t.startswith(" Standings after") for t in said(rig))
    assert rig.store.deleted == 1 and rig.keys.answers == []


def test_a_season_that_ends_in_pog_deletes_its_files_says_so_and_starts_a_new_one(tmp_path):
    rig = program_rig(tmp_path, [ENTER] + COACH_AND_TEAM + EXIT, preset=preset_season(gtp=17), outcomes=[played(3, 30)],
                      pog=lambda r: setattr(r.game.season, "gtp", 0))
    rig.game.season.records.win(2, 2)
    rig.run()
    spoken = said(rig)
    assert rig.store.deleted == 1 and rig.store.calls.index("delete_season_files") > 0
    assert spoken.index(P.SEASON_OVER) < spoken.index(T.ENTER_COACH) < spoken.index(" kim choose your team ")
    # the new season: week 1, the new coach, no record left, the menu again
    assert spoken.count(WEEK % 1) == 1 and spoken.count(" kim select ") == 1
    season = rig.game.season
    assert season.gtp == 1 and season.coach == "kim" and season.records.record(2, 2) == (0, 0)
    assert season.playoffs.pairings == [] and len(season.schedule) == 16
    assert rig.keys.answers == [] and not any(t.startswith(" Standings after") for t in spoken)


def test_the_new_season_begins_with_the_week_line_the_log_stays_open(tmp_path):
    rig = program_rig(tmp_path, [ENTER] + COACH_AND_TEAM + EXIT, preset=preset_season(gtp=17), outcomes=[played(3, 30)],
                      pog=lambda r: setattr(r.game.season, "gtp", 0)).run()
    assert said(rig).count(WEEK % 1) == 1                            # the first week of the new season
    assert [c for c in rig.store.calls if isinstance(c, tuple)] == [("open_log", False)]


def test_the_engine_s_player_won_flag_starts_again_with_a_new_season(tmp_path):
    rig = program_rig(tmp_path, [ENTER] + COACH_AND_TEAM + EXIT, preset=preset_season(gtp=17), outcomes=[played(3, 30)],
                      pog=lambda r: setattr(r.game.season, "gtp", 0))
    rig.game.season_engine.player_won = True
    rig.run()
    assert rig.game.season_engine.player_won is False
