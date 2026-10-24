"""NX-B1 (the owner's bug report of 2026-10-24, D-142, D-143): "I should get to determine what player will start at the beginning of the week if a
player is injured." (nfl4 only, rule 0.13). When a man of the player's team will not play the week's game (out, or resting), the to-do list asks who
starts in his place, the staff's choice (the next man up) first so Enter keeps the pace; F9's injury report has the same choice; the choice holds until
he is fit again; with the staff setting on nothing is asked. The chosen man plays the place at replacement level (INJ-2 is unchanged).
"""
import json
import random

from drrig import SURNAMES
from frrig import COACH_AND_TEAM, DOWN, ENTER, ESC, F9, WANT_FRANCHISE, franchise_rig, quit_policy, run_until, spoken

from nfl4.extras import nx_texts as X
from nfl4.extras import tuning as T
from nfl4.extras.franchise import data as D
from nfl4.extras.franchise import history
from nfl4.extras.franchise import injuries as I
from nfl4.extras.franchise import injury_flow as F
from nfl4.extras.franchise import todo
from nfl4.extras.franchise.league import LeagueError, LeagueRecord, new_league
from nfl4.game.rnd import GameRandom

import pytest

TEAM = 5
WORDS = history.Words(lambda team: "Team%d" % team)
GAME = [ENTER, ENTER, ENTER]


def league_at(week, seed=3):
    league = new_league(GameRandom(random.Random(seed)), SURNAMES, "Kim", TEAM, "20260101-000000")
    league.gtp = week
    return league


def dl(league, k=0):
    return league.player_at(TEAM, D.PLACES_OF["DL"][k])


# ----- the rules -----

def test_the_staffs_choice_is_first_then_the_fit_men_of_the_group_the_best_first():
    league = league_at(3)
    hurt = dl(league)
    I.injure(league, hurt.id, "IJA", 5, 0, 2)                         # hurt in week 2: out in week 3
    choices = I.cover_choices(league, hurt.id, 3)
    staff_table = I.lineup(league, TEAM, 3, staff=False, use_chosen=False)
    assert choices[0].id == staff_table[hurt.place][0] == dl(league, 1).id         # the next man up
    rest = choices[1:]
    assert {p.id for p in rest} == {dl(league, k).id for k in range(2, 6)}
    assert [p.rating for p in rest] == sorted((p.rating for p in rest), reverse=True)
    assert I.to_choose(league, 3) == [hurt.id]


def test_the_chosen_man_plays_the_place_and_the_staff_setting_or_another_team_ignores_the_choice():
    league = league_at(3)
    hurt = dl(league)
    I.injure(league, hurt.id, "IJA", 5, 0, 2)
    pick = I.cover_choices(league, hurt.id, 3)[-1]
    I.choose(league, hurt.id, pick.id)
    table = I.lineup(league, TEAM, 3, staff=False)
    assert table[hurt.place][:2] == (pick.id, pick.name)
    assert table[hurt.place][2] == min(pick.rating, I.stand_in_rating("DL"))       # replacement level, as for the staff's man (INJ-2)
    assert I.lineup(league, TEAM, 3, staff=True)[hurt.place][0] == dl(league, 1).id       # the staff handles it: the staff's rule
    assert I.effective_sum(league, TEAM, 3) == I.effective_sum(league, TEAM, 3, staff=True)
    I.choose(league, hurt.id, None)
    assert league.injuries["chosen"] == [] and I.lineup(league, TEAM, 3, staff=False)[hurt.place][0] == dl(league, 1).id


def test_a_choice_who_cannot_play_falls_back_to_the_staffs_rule():
    league = league_at(3)
    hurt = dl(league)
    I.injure(league, hurt.id, "IJA", 5, 0, 2)
    pick = I.cover_choices(league, hurt.id, 3)[-1]
    I.choose(league, hurt.id, pick.id)
    table = I.lineup(league, TEAM, 3, staff=False, out=frozenset({pick.id}))       # hurt in the game in progress
    assert table[hurt.place][0] == dl(league, 1).id


def test_the_choice_ends_when_he_is_back():
    league = league_at(3)
    hurt = dl(league)
    I.injure(league, hurt.id, "IJA", 1, 0, 2)                         # back in week 3... misses week 3 only
    I.choose(league, hurt.id, dl(league, 3).id)
    I.settle(league, 4, GameRandom(random.Random(1)), SURNAMES)
    assert league.injuries["chosen"] == []


def test_a_returners_choices_are_the_backs_and_receivers_who_play_but_not_the_other_returner():
    league = league_at(3)
    ret = league.player_at(TEAM, D.PLACES_OF["RET"][0])
    other = league.player_at(TEAM, D.PLACES_OF["RET"][1])
    I.injure(league, ret.id, "IJA", 5, 0, 2)
    choices = I.cover_choices(league, ret.id, 3)
    assert choices and all(p.pos in ("RB", "WR") for p in choices) and other.id not in {p.id for p in choices}
    I.choose(league, ret.id, choices[-1].id)
    assert I.lineup(league, TEAM, 3, staff=False)[ret.place][0] == choices[-1].id


def test_nothing_to_choose_when_he_plays_or_for_another_team():
    league = league_at(3)
    hurt = dl(league)
    I.injure(league, hurt.id, "IJA", 1, 0, 2)                         # questionable in week 3
    assert I.cover_choices(league, hurt.id, 3)                        # he rests unless the player says so
    I.decide(league, hurt.id, 3, True)
    assert I.cover_choices(league, hurt.id, 3) == [] and I.to_choose(league, 3) == []
    theirs = league.player_at(9, D.PLACES_OF["DL"][0])
    I.injure(league, theirs.id, "IJA", 5, 0, 2)
    assert I.cover_choices(league, theirs.id, 3) == []


def test_the_item_answers_the_staffs_choice_keeps_none_another_keeps_him():
    league = league_at(3)
    hurt = dl(league)
    I.injure(league, hurt.id, "IJA", 5, 0, 2)
    item = F.lineup_item(league, 3, hurt.id)
    league.todo.append(item)
    situation, answers = F.lineup_view(WORDS, league, item)
    assert situation == [X.text("NXI-60", player=hurt.name, position=WORDS.position("DL"))]
    assert answers[0].endswith("the staff's choice") and len(answers) == todo.answer_count(league, item) == 5
    assert todo.is_do_nothing(league, item, 0) and not todo.is_do_nothing(league, item, 2)
    chosen = todo.apply_answer(league, item, 2)
    assert league.injuries["chosen"] == [[hurt.id, chosen.id]] and item not in league.todo
    second = F.lineup_item(league, 3, hurt.id)
    league.todo.append(second)
    todo.apply_answer(league, second, 0)
    assert league.injuries["chosen"] == []


def test_the_file_keeps_the_choice_and_an_older_file_has_none():
    league = league_at(3)
    hurt = dl(league)
    I.injure(league, hurt.id, "IJA", 5, 0, 2)
    I.choose(league, hurt.id, dl(league, 4).id)
    data = json.loads(league.to_json())
    assert data["format"] == D.FORMAT >= 15 and data["injuries"]["chosen"] == [[hurt.id, dl(league, 4).id]]
    data["format"] = 14
    del data["injuries"]["chosen"]
    assert D.FORMAT >= 15                                              # (the loads of both formats: the program test below, a whole league)


@pytest.mark.parametrize("bad", [[[1]], [[10 ** 10, 1]], "x", [[1, 1]]])
def test_a_bad_choice_is_damage(bad):
    league = league_at(3)
    hurt = dl(league)
    I.injure(league, hurt.id, "IJA", 5, 0, 2)
    league.injuries["chosen"] = bad if bad != [[1, 1]] else [[hurt.id, hurt.id]]
    with pytest.raises(LeagueError):
        league.check()


# ----- the program: the week's to-do list, the staff setting, F9 -----

def hurt_own_lineman(monkeypatch):
    """The player's first defensive lineman hurt in week 1 for five games: out in week 2. No extra-work item, so the week's list is the who-starts item."""
    monkeypatch.setattr(T, "FR_EXTRA_WORK_WEEKS", ())
    real = I.after_games

    def draws(league, week, rnd, surnames, played=()):
        done = real(league, week, rnd, surnames, played)
        if week == 1:
            man = league.player_at(league.team, D.PLACES_OF["DL"][0])
            I.injure(league, man.id, "IJA", 5, 0, 1)
            I.settle(league, 2, rnd, surnames)
        return done
    monkeypatch.setattr(I, "after_games", draws)


def run(tmp_path, keys, setup=None):
    rig = franchise_rig(tmp_path, WANT_FRANCHISE + COACH_AND_TEAM + keys, policy=quit_policy)
    if setup is not None:
        setup(rig)
    return run_until(rig)


def own_dl(rig):
    league = rig.fstore.league
    return league.player_at(league.team, D.PLACES_OF["DL"][0])


def test_the_week_asks_who_starts_and_the_second_answer_starts_him_in_the_game(tmp_path, monkeypatch):
    hurt_own_lineman(monkeypatch)
    seen = []
    real = F.lineup_roster

    def roster(league, team, week, staff):
        if team == league.team:
            seen.append(I.lineup(league, team, week, staff)[own_dl_place(league)])
        return real(league, team, week, staff)
    monkeypatch.setattr(F, "lineup_roster", roster)
    rig = run(tmp_path, GAME + [DOWN, ENTER] + GAME)
    league = rig.fstore.league
    hurt = own_dl(rig)
    text = spoken(rig)
    asked = [t for t in text if X.text("NXI-60", player=hurt.name, position=WORDS.position("DL")).strip() in t]
    assert asked, "the to-do list asks who starts"
    (row,) = league.injuries["chosen"] or [[None, None]]
    chosen = league.players[row[1]]
    assert X.text("NXI-61", get=chosen.name, give=hurt.name) in text
    assert seen and seen[-1][0] == chosen.id                           # the week 2 game's lineup has him in the place
    saved = LeagueRecord.from_json(rig.files.data["league.sav"].decode("utf-8"))
    assert saved.injuries["chosen"] == league.injuries["chosen"]
    data = json.loads(rig.files.data["league.sav"].decode("utf-8"))
    data["format"] = 14                                                # a league saved by 0.13.0: no choice, the staff's rule
    del data["injuries"]["chosen"]
    data["todo"] = [i for i in data["todo"] if i["kind"] != D.TODO_LINEUP]
    assert LeagueRecord.from_json(json.dumps(data)).injuries["chosen"] == []


def own_dl_place(league):
    return D.PLACES_OF["DL"][0]


def test_enter_keeps_the_staffs_choice(tmp_path, monkeypatch):
    hurt_own_lineman(monkeypatch)
    rig = run(tmp_path, GAME + [ENTER])
    league = rig.fstore.league
    assert league.injuries["chosen"] == [] and not [i for i in league.todo if i["kind"] == D.TODO_LINEUP]


def test_with_the_staff_setting_on_nothing_is_asked(tmp_path, monkeypatch):
    hurt_own_lineman(monkeypatch)

    def staff_on(rig):
        rig.game.options.settings.game.nx_fr_auto = True
    rig = run(tmp_path, GAME, setup=staff_on)
    hurt = own_dl(rig)
    assert not any(X.text("NXI-60", player=hurt.name, position=WORDS.position("DL")).strip() in t for t in spoken(rig))
    assert rig.fstore.league.injuries["chosen"] == []


def test_f9s_injury_report_has_the_row_and_enter_chooses(tmp_path, monkeypatch):
    hurt_own_lineman(monkeypatch)
    to_report = [F9] + [DOWN] * 4 + [ENTER] + [DOWN] * 8 + [ENTER]     # F9, Franchise, injury report (the 9th item)
    keys = GAME + to_report + [DOWN, ENTER, DOWN, DOWN, ENTER, ESC, ESC, ESC]   # the row after him, the third choice
    rig = run(tmp_path, keys)
    league = rig.fstore.league
    hurt = own_dl(rig)
    text = spoken(rig)
    assert any(X.text("NXI-63", player=hurt.name).strip() in t for t in text)
    (row,) = league.injuries["chosen"]
    assert row[0] == hurt.id and X.text("NXI-61", get=league.players[row[1]].name, give=hurt.name) in text
    assert not [i for i in league.todo if i["kind"] == D.TODO_LINEUP]          # the item about his place is answered


def test_the_help_says_you_choose_who_starts():
    assert "choose who starts" in X.text("NXH-42") and len(X.text("NXH-42")) <= 200
