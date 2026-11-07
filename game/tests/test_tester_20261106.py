"""A tester's e-mail of 2026-11-06, made the owner's own (nfl4 only, rule 0.13; rule 0.40; D-214 to D-216):

1. "Add injured reserved to franchise mode. Include the ability to bring people off injured reserve including activations." (reserve.py, reserve_flow.py)
2. "First Safety and free safety are two different positions. It groups all safeties as one this is incorrect. Second kick returners aren't tradable
   this is incorrect. All linebackers need to be properly separated as well." (positions.py; trades.group)
3. "It uses two different whistles this should be fixed. it should only use the whistle that claude made or a custom whistle sound file provided by
   the user." (GameSounds.own_whistle, Stadium.whistle)
"""
import json
import os
import random
from types import SimpleNamespace

import pytest

from nfl4.extras import nfl_surnames
from nfl4.extras import nx_texts as X
from nfl4.extras import real_names as R
from nfl4.extras import roster_model as RM
from nfl4.extras import stadium as ST
from nfl4.extras import tuning as T
from nfl4.extras.franchise import data as D
from nfl4.extras.franchise import history
from nfl4.extras.franchise import injuries as I
from nfl4.extras.franchise import positions as PS
from nfl4.extras.franchise import real_roster as RR
from nfl4.extras.franchise import reserve as RV
from nfl4.extras.franchise import reserve_flow as RVF
from nfl4.extras.franchise import trades as TR
from nfl4.extras.franchise.league import LeagueError, LeagueRecord, new_league
from nfl4.game.rnd import GameRandom

TEAM = 6
WORDS = history.Words(lambda team: "Team%d" % team)


def real_league(week=3, seed=3):
    league = new_league(GameRandom(random.Random(seed)), nfl_surnames.pool(), "Kim", TEAM, "20260101-000000", real=R.defaults())
    league.gtp = week
    return league


def make_room(league, places=1):
    """Release the lowest rated healthy men until the 53 has room (a real team may start above 53 before its cut)."""
    while RR.room(league, TEAM) < places:
        man = min((p for p in league.team_men(TEAM) if I.healthy(league, p.id, league.gtp) and p.pos == "WR"), key=lambda p: (p.rating, p.id))
        RR.leave(league, man, "free")
        man.team = 0


def hurt_man(league, games=8, week=None):
    """A healthy starter of the player's team, hurt in the game before `week` for `games` games."""
    week = league.gtp if week is None else week
    man = next(p for p in league.team_men(TEAM) if p.position == "WR" and p.place >= 0)
    I.injure(league, man.id, "IJL", games, 0, week - 1)
    return man


# ----- 1: injured reserve -----

def test_a_hurt_man_goes_on_injured_reserve_and_frees_his_place_on_the_53():
    league = real_league()
    man = hurt_man(league)
    count = RR.roster_count(league, TEAM)
    assert RV.place_problem(league, man, 3) is None
    RV.place(league, man, 3)
    assert (man.status, man.roster_list, man.place) == ("list", "IR", -1) and RR.roster_count(league, TEAM) == count - 1
    assert man.id not in [pid for ids in league.chart[TEAM - 1].values() for pid in ids]
    assert RV.row_of(league, man.id) == [man.id, 3, 0, 0] and man in RV.on_list(league)
    healthy = next(p for p in league.team_men(TEAM) if I.healthy(league, p.id, 3))
    assert RV.place_problem(league, healthy, 3) == "not hurt"


def test_designate_after_two_games_then_activate_after_four_when_healthy():
    league = real_league()
    man = hurt_man(league, games=4)                                   # hurt in week 2: back in week 7
    RV.place(league, man, 3)
    league.gtp = 4
    assert RV.designate_problem(league, man, 4) == "too early"        # one game missed
    league.gtp = 5
    assert RV.designate_problem(league, man, 5) is None
    RV.designate(league, man, 5)
    assert man.roster_list == "IRD" and RV.returns_used(league) == 1 and RV.window_left(league, man, 5) == T.FR_IR_WINDOW_WEEKS
    league.gtp = 6
    assert RV.activate_problem(league, man, 6) == "too early"         # three games missed
    league.gtp = 7
    make_room(league)
    assert RV.missed(league, man, 7) == 4 and I.healthy(league, man.id, 7)
    assert RV.activate_problem(league, man, 7) is None
    RV.activate(league, man, 7)
    assert (man.status, man.roster_list) == ("active", "") and RV.row_of(league, man.id) is None
    assert man.id in league.chart[TEAM - 1]["WR"]


def test_a_man_still_hurt_is_not_activated_and_a_closed_window_ends_his_season():
    league = real_league()
    man = hurt_man(league, games=12)
    RV.place(league, man, 3)
    RV.designate(league, man, 5)
    assert RV.activate_problem(league, man, 7) == "still hurt"
    closed = RV.close_windows(league, 8)
    assert closed == [man] and man.roster_list == "IR" and RV.ended(league, man, 8)
    assert RV.designate_problem(league, man, 9) == "out for the season"
    assert RVF.report_lines(league, 9) == []                          # said once, the week it closed


def test_eight_returns_a_season_two_more_in_the_play_offs_and_one_man_twice_at_most():
    league = real_league()
    assert RV.returns_allowed(league, 5) == T.FR_IR_RETURNS == 8 and RV.returns_allowed(league, league.regular_weeks + 1) == 10
    RV.record(league)["returns"] = [[1, 2]] * 8
    man = hurt_man(league)
    RV.place(league, man, 3)
    assert RV.designate_problem(league, man, 5) == "no returns left"
    RV.record(league)["returns"] = [[man.id, 2], [man.id, 3]]
    assert RV.designate_problem(league, man, 5) == "he returned twice"


def test_activating_with_a_full_53_asks_for_a_release_who_keeps_the_family_minimums():
    league = real_league()
    man = hurt_man(league, games=1)
    RV.place(league, man, 3)
    while RR.room(league, TEAM) > 0:                                  # fill the 53 with a free agent at a time
        agent = next(p for p in league.players.values() if p.status == "free")
        RR.join(league, TEAM, agent)
    RV.designate(league, man, 5)
    assert RV.activate_problem(league, man, 7) == "no room"
    choices = RV.releasable(league, man, 7)
    assert choices and all(I.healthy(league, p.id, 7) for p in choices)
    gone = choices[0]
    RV.activate(league, man, 7, gone)
    assert man.status == "active" and gone.status == "free" and gone.team == 0 and RR.room(league, TEAM) == 0


def test_the_computer_teams_are_not_moved_and_their_real_lists_stay():
    league = real_league()
    before = [(p.id, p.status, p.roster_list) for p in league.players.values() if p.team != TEAM]
    man = hurt_man(league)
    RV.place(league, man, 3)
    assert [(p.id, p.status, p.roster_list) for p in league.players.values() if p.team != TEAM] == before


def test_format_21_round_trips_the_reserve_and_a_format_20_file_gets_an_empty_one():
    league = real_league()
    man = hurt_man(league)
    RV.place(league, man, 3)
    RV.designate(league, man, 5)
    league.gtp = 1                                                    # (a whole record without a schedule is one of week 1)
    data = json.loads(league.to_json())
    assert data["format"] == D.FORMAT == 21 and data["injuries"]["reserve"] == {"placed": [[man.id, 3, 5, 0]], "returns": [[man.id, 5]]}
    assert LeagueRecord.from_json(json.dumps(data)).injuries["reserve"] == data["injuries"]["reserve"]
    data = json.loads(real_league(week=1).to_json())               # a league where the player placed nobody, saved by 0.16.17 (format 20)
    del data["injuries"]["reserve"]
    data["format"] = 20
    assert LeagueRecord.from_json(json.dumps(data)).injuries["reserve"] == {"placed": [], "returns": []}


@pytest.mark.parametrize("bad", [None, {"placed": []}, {"placed": [[1, 2, 3]], "returns": []}, {"placed": [], "returns": [[1]]}])
def test_a_damaged_reserve_record_is_damage(bad):
    data = json.loads(real_league().to_json())
    data["injuries"]["reserve"] = bad
    with pytest.raises(LeagueError):
        LeagueRecord.from_json(json.dumps(data))


def test_the_menus_lines_and_rules_have_no_placeholder_left_and_name_the_numbers():
    league = real_league()
    man = hurt_man(league)
    RV.place(league, man, 3)
    RV.designate(league, man, 5)
    line = RVF.list_line(WORDS, league, man, 6)
    assert "<" not in line and "injured reserve since week 3, 3 games missed, designated to return, 2 weeks left" in line and "practice window" in line
    rules = " ".join(RVF.rules_lines())
    assert "<" not in rules and " 4 games" in rules and " 8 returns" in rules and " 2 more in the play-offs" in rules
    assert X.text("NXI-R01") == "injured reserve"


# ----- 2: the positions -----

def test_the_menus_offer_free_and_strong_safeties_and_three_linebackers_apart():
    assert {"FS", "SS", "SAM", "MIKE", "WILL", "LEDG", "REDG"} <= set(PS.ALL) and len(PS.ALL) == 22
    words = [PS.word(code) for code in PS.WITH_RETURNERS]
    assert len(set(words)) == len(words) == 23
    assert PS.word("FS") == "free safeties" and PS.word("SS") == "strong safeties" and PS.word("MIKE") == "middle linebackers"
    assert PS.word("SAM") == "strong-side linebackers" and PS.word("WILL") == "weak-side linebackers" and PS.word("KR") == "kick and punt returners"


def test_a_position_lists_only_its_own_men():
    league = real_league()
    for code in ("FS", "SS", "SAM", "MIKE", "WILL"):
        men = PS.men(league, TEAM, code, lambda family: TR.group(league, TEAM, family, bench=True))
        assert all(PS.position_of(p) == code for p in men)
    free = PS.men(league, TEAM, "FS", lambda family: TR.group(league, TEAM, family, bench=True))
    strong = PS.men(league, TEAM, "SS", lambda family: TR.group(league, TEAM, family, bench=True))
    assert free and strong and not {p.id for p in free} & {p.id for p in strong}


def test_kick_returners_are_in_the_trade_lists():
    league = real_league()
    back = PS.returners(league, TEAM)
    assert back
    for man in back:
        assert man in TR.group(league, TEAM, man.pos, bench=True)       # before D-214 a man of a return place was in no list
    other = 1 if TEAM != 1 else 2
    theirs = PS.men(league, other, PS.RETURNERS, None)
    assert theirs and all(p.team == other and p.status == "active" for p in theirs)


def test_a_trade_proposal_may_give_a_man_of_another_family():
    league = real_league()
    league.gtp = 5
    get = PS.returners(league, 1)[0]
    give = next(p for p in league.team_men(TEAM) if p.pos != get.pos and p.place >= 0 and p.pos not in ("QB", "K", "P"))
    trade, _added = TR.propose(league, TEAM, give, get, (), (), league.records, 5)
    assert trade is None or (trade.give_a, trade.give_b) == (give.id, get.id)      # the value rule answers; the family no longer refuses it


# ----- 3: one whistle -----

def test_the_owners_mode_plays_the_made_whistle_with_the_stadium_off_and_classic_keeps_the_original(tmp_path):
    from gamerig import Rig
    from nfl4.audio.output import SLOT_TACKLE
    rig = Rig([], sounds_dir=tmp_path)
    sounds = rig.game.sounds
    sounds.whistle_hook = None
    sounds.own_mode = lambda: True
    before = len(rig.slot_log)
    sounds.play_tackle(8)
    played = [e for e in rig.slot_log[before:] if e.action == "play" and e.slot == SLOT_TACKLE]
    assert [e.sound_id for e in played] == ["file whistle.wav"]
    sounds.own_mode = lambda: False
    before = len(rig.slot_log)
    sounds.play_tackle(8)
    assert [e.sound_id for e in rig.slot_log[before:] if e.action == "play" and e.slot == SLOT_TACKLE] == ["snd_foot11"]


def test_the_players_whistle_replaces_the_made_one_everywhere(tmp_path, monkeypatch):
    mine = tmp_path / "mine"
    mine.mkdir()
    (mine / "whistle.wav").write_bytes(b"x")
    monkeypatch.setattr(ST, "player_folder", lambda: str(mine))
    sounds = SimpleNamespace(audio=SimpleNamespace(library=None))
    from nfl4.game.sounds import GameSounds
    assert GameSounds.own_whistle(sounds_with(sounds)) == str(mine / "whistle.wav")
    assert os.path.exists(os.path.join(ST.shipped_folder(), "whistle.wav"))


def sounds_with(ns):
    from nfl4.game.sounds import GameSounds
    ns.slot_files = lambda name: GameSounds.slot_files(ns, name)
    return ns


def test_put_back_also_moves_the_old_kinds_of_whistle_aside(tmp_path):
    (tmp_path / "whistle_short.wav").write_bytes(b"y")
    (tmp_path / "whistle.wav").write_bytes(b"y")
    assert sorted(ST.put_back(str(tmp_path)).moved) == ["whistle.wav", "whistle_short.wav"]


def test_madden_s_linebackers_are_one_middle_and_two_outside():
    assert RM.FAMILY_POSITIONS["backers"] == ("SAM", "MIKE", "WILL") and RM.FAMILY_POSITIONS["safeties"] == ("FS", "SS")


# ----- F9 on the program rig -----

def test_f9_franchise_injured_reserve_opens_after_the_injury_report_and_says_its_rules(tmp_path):
    from frrig import COACH_AND_TEAM, DOWN, ENTER, ESC, F9, WANT_FRANCHISE, franchise_rig, quit_policy, run_until, spoken
    keys = [F9] + [DOWN] * 4 + [ENTER] + [DOWN] * 9 + [ENTER, DOWN, DOWN, ENTER, ESC, ESC, ESC, ESC, ESC]   # F9, Franchise, injured reserve (10th), the rules
    rig = franchise_rig(tmp_path, WANT_FRANCHISE + COACH_AND_TEAM + keys, policy=quit_policy)
    run_until(rig)
    text = spoken(rig)
    assert any(t.startswith(X.text("NXI-R02", n=0, m=8)) for t in text), text[-12:]
    assert any(RVF.rules_lines()[0].strip() in t for t in text)
