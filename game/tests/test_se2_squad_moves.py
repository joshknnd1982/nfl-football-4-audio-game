"""S-E2 (D-200, Q-067, D-162, D-174; nfl4 only, rule 0.13): other teams sign practice squad players, and every team protects four squad men a week.
This is inspired by Jim Kitchen.

The NFL's rules (squad_moves.py, spec/NFL_EXTRA_FEATURES section 23): a club may sign another club's squad man to its roster (never to its squad),
except the four that club protects this week and the men of the squad of the team it plays this week. The game: a computer team whose family is short
for the coming weeks signs one squad man (its own, or another team's when he is clearly better), with a release that keeps every family's minimum, the
cap, no draw; a computer squad that lost a man fills it from the free agents; the player protects his own four (the staff's best four until he
chooses), may sign another team's man himself, hears when one of his is taken and can hear the season's signings; league.sav format 20.
"""
import json
import random
from types import SimpleNamespace

import pytest

from nfl4.extras import nfl_surnames
from nfl4.extras import nx_texts as X
from nfl4.extras import real_names as R
from nfl4.extras import tuning as T
from nfl4.extras.franchise import contracts as CT
from nfl4.extras.franchise import data as D
from nfl4.extras.franchise import history
from nfl4.extras.franchise import injuries as I
from nfl4.extras.franchise import practice as P
from nfl4.extras.franchise import practice_flow as PF
from nfl4.extras.franchise import real_roster as RR
from nfl4.extras.franchise import signings as S
from nfl4.extras.franchise import squad_moves as M
from nfl4.extras.franchise import squad_moves_flow as MF
from nfl4.extras.franchise.league import SEASON, LeagueError, LeagueRecord, new_league, team_ref
from nfl4.game.keys import KEY_DOWN, KEY_ENTER, KEY_ESCAPE
from nfl4.game.rnd import GameRandom

BEARS = 17
WEEK = 2                     # the week whose preparation makes the signings (the first that has one)
ENTER, ESC, DOWN = KEY_ENTER, KEY_ESCAPE, KEY_DOWN


@pytest.fixture(autouse=True)
def fresh_defaults():
    R.reset_defaults_cache()
    nfl_surnames._SHIPPED = None
    yield
    R.reset_defaults_cache()
    nfl_surnames._SHIPPED = None


class Speech:
    def __init__(self):
        self.said = []

    def stop(self):
        pass

    def say_async(self, text):
        self.said.append(text)


class Keys:
    def __init__(self, *answers):
        self.answers = list(answers)

    def read_key(self):
        return self.answers.pop(0) if self.answers else ESC


def real_league(seed=3, team=BEARS):
    league = new_league(GameRandom(random.Random(seed)), nfl_surnames.pool(), "Kim", team, "20260101-000000", real=R.defaults())
    league.stage, league.gtp = SEASON, 1                                    # the whole check of week 1; the signings run for WEEK
    league.prepared = [league.season, league.gtp]
    division, place = team_ref(3)
    league.schedule = [[division, place, 1] for _ in range(league.regular_weeks)]     # the player's games (all against team 3: a test's schedule)
    return league


def franchise(league, playing=False):
    store = SimpleNamespace(league=league, saves=0)
    store.words = history.Words(lambda t: "Team %d" % t, lambda: store.league)
    store.save = lambda: setattr(store, "saves", store.saves + 1)
    game = SimpleNamespace(play_engine=object() if playing else None, real_names=R.defaults(), customization=None, options=None)
    return game, store


def hurt_family(league, team, family, keep=1, games=6, week=1):
    """All but `keep` men of the team's family hurt for `games` games from the week after `week` (the best kept)."""
    men = sorted((p for p in RR.members(league, team) if p.pos == family), key=lambda p: (-p.rating, p.id))
    kind = I.kinds_for(family)[0][0]
    for p in men[keep:]:
        I.injure(league, p.id, kind, games, 0, week)
    return men[keep:]


def first_in_turn(league, week=None):
    """The computer team that signs first in the week's turn (squad_moves.week_signings: a turn that changes each week)."""
    week = WEEK if week is None else week
    start = (league.season * 7 + week) % D.TEAMS
    return next((start + k) % D.TEAMS + 1 for k in range(D.TEAMS) if (start + k) % D.TEAMS + 1 != BEARS)


def squad_man(league, team, family, rating):
    """A man of the team's squad made a man of `family` with `rating` (a test's setup: the first squad man of no other use)."""
    man = next(p for p in P.squad(league, team) if p.pos == family) if any(p.pos == family for p in P.squad(league, team)) else None
    if man is None:
        raise AssertionError("no squad man of %s on team %d" % (family, team))
    man.rating = rating
    return man


# ----- the protections -----

def test_the_staff_protects_each_teams_four_best_and_the_player_chooses_his_own():
    league = real_league()
    for team in (1, 2, BEARS):
        best = [p.id for p in P.squad(league, team)][:M.PROTECT]
        assert M.protected_ids(league, team) == set(best)
    assert M.staff_protects(league)
    squad = P.squad(league, BEARS)
    weakest = squad[-1]
    assert M.set_protected(league, weakest, True) == "four protected"         # the staff's four are his four until he ends one
    assert M.set_protected(league, squad[0], False) is None
    assert M.set_protected(league, weakest, True) is None
    assert M.protected_ids(league, BEARS) == {p.id for p in squad[1:4]} | {weakest.id}
    assert not M.staff_protects(league)
    assert M.set_protected(league, P.squad(league, 1)[0], True) == "not a player of the practice squad"
    league.check()
    again = LeagueRecord.from_json(league.to_json())
    assert again.practice["protected"] == league.practice["protected"] and again.to_json() == league.to_json()


def test_a_protected_man_who_left_the_squad_no_longer_counts():
    league = real_league()
    squad = P.squad(league, BEARS)
    M.set_protected(league, squad[0], False)
    P.release_from_squad(league, squad[1])
    assert squad[1].id not in M.protected_ids(league, BEARS) and len(M.protected_ids(league, BEARS)) == 2
    assert M.set_protected(league, squad[5], True) is None and len(M.protected_ids(league, BEARS)) == 3
    league.check()


def test_signable_leaves_out_the_protected_the_stand_ins_the_own_squad_and_the_next_opponent():
    league = real_league()
    weeks = [[] for _ in range(18)]
    weeks[league.gtp - 1] = [[1, 2], [3, BEARS]]
    league.calendar = {"label": "test", "weeks": weeks}
    assert M.next_opponent(league, 1, league.gtp) == 2 and M.next_opponent(league, BEARS, league.gtp) == 3 and M.next_opponent(league, 4, league.gtp) == 0
    stand = P.squad(league, 5)[6]
    league.injuries["stand_ins"].append([5, stand.pos, stand.name, stand.rating])
    men = M.signable(league, 1, league.gtp)
    teams = {p.team for p in men}
    assert 1 not in teams and 2 not in teams and teams                       # its own squad and this week's opponent's
    for team in teams:
        assert not {p.id for p in men if p.team == team} & M.protected_ids(league, team)
    assert stand not in men and men == sorted(men, key=lambda p: (-p.rating, p.id))
    first = P.squad(league, BEARS)[0]
    assert first not in M.signable(league, 1, league.gtp)
    M.set_protected(league, first, False)                                   # the player's own choice counts for his men
    assert first in M.signable(league, 1, league.gtp) and first not in M.signable(league, 3, league.gtp)


def test_the_weeks_protections_are_fixed_before_the_first_signing():
    league = real_league()
    week = M.week_protections(league)
    nine = P.squad(league, 9)
    late = nine[-1]
    late.rating = 99                                                         # (a squad that changes during the week's signings)
    assert late.id in M.protected_ids(league, 9)                             # as it stands now he would be protected
    men = M.signable(league, 1, WEEK, protections=week)
    assert late in men and not {p.id for p in men} & week[9]                 # the week's list: he is not, the four named before are


# ----- the computer teams' weekly signings -----

def test_a_team_short_for_weeks_signs_a_squad_man_of_the_family_and_draws_nothing():
    league = real_league()
    team = 1
    gone = hurt_family(league, team, "QB", keep=1)
    assert gone and M.need_of(league, team, WEEK) == "QB"
    before = sorted(p.id for p in RR.members(league, team))
    rows = M.week_signings(league, WEEK)
    mine = [row for row in rows if row[2] == team]
    assert len(mine) == 1
    man = league.players[mine[0][3]]
    assert man.status == "active" and man.team == team and man.pos == "QB" and man.years == 1 and man.salary == CT.min_salary(man.seasons)
    assert M.need_of(league, team, WEEK) is None
    assert len(RR.members(league, team)) <= D.ROSTER_MAX and sorted(p.id for p in RR.members(league, team)) != before
    for group, least in T.FR_FAMILY_MIN.items():                             # a release never takes a family under its minimum
        assert M.able(league, team, group, WEEK) >= min(least, M.able(league, team, group, WEEK))
    assert league.practice["signings"][-1] == mine[0]
    league.check()


def test_the_same_league_makes_the_same_signings_and_no_draw_is_made():
    a, b = real_league(), real_league()
    for league in (a, b):
        hurt_family(league, 1, "QB")
        hurt_family(league, 9, "CB", keep=1)
        hurt_family(league, 20, "K", keep=0)
    rnd_state = random.getstate()
    assert M.week_signings(a, WEEK) == M.week_signings(b, WEEK)
    assert random.getstate() == rnd_state and a.to_json() == b.to_json()


def poach_setup(edge_rating):
    """A team short of corners whose own squad corners are rated 50, and one man of another team's squad made a corner rated `edge_rating`, the
    weakest of that squad (the others rated 90, so he is never among the four it protects); every other squad corner rated 41."""
    league = real_league()
    team = first_in_turn(league)
    other_team = 9 if team != 9 else 10
    hurt_family(league, team, "CB", keep=1)
    for p in league.players.values():
        if p.status == P.STATUS and p.pos == "CB":
            p.rating = 50 if p.team == team else 41
    squad = P.squad(league, other_team)
    target = squad[-1]
    for p in squad:
        p.rating = 90
    target.pos, target.position, target.rating = "CB", "CB", edge_rating
    assert target.id not in M.protected_ids(league, other_team) and any(p.pos == "CB" for p in P.squad(league, team))
    return league, team, other_team, target


def test_another_teams_man_is_taken_only_when_clearly_better_and_never_a_protected_one():
    league, team, other_team, target = poach_setup(50 + T.FR_SQUAD_POACH_EDGE - 1)
    row = next(r for r in M.week_signings(league, WEEK) if r[2] == team)
    assert row[1] == team and target.team != team                           # not better by the edge: his own man (a later team may take him)
    league, team, other_team, target = poach_setup(50 + T.FR_SQUAD_POACH_EDGE)
    row = next(r for r in M.week_signings(league, WEEK) if r[2] == team)
    assert row[1] == other_team and row[3] == target.id and target.team == team and target.status == "active"
    assert all(league.players[r[3]].id not in M.week_protections(league).get(r[1], set()) for r in league.practice["signings"] if r[1] != r[2])
    league.check()


def test_the_player_hears_when_another_team_signs_his_man_and_a_protected_man_is_never_taken():
    league = real_league()
    game, store = franchise(league)
    team = first_in_turn(league)
    hurt_family(league, team, "WR", keep=2)
    for p in league.players.values():
        if p.status == P.STATUS and p.pos == "WR":
            p.rating = 41
    M.set_protected(league, P.squad(league, BEARS)[0], True)                # his four now (the staff's), so the star below stays unprotected
    star = next(p for p in P.squad(league, BEARS) if p.id not in M.protected_ids(league, BEARS))
    star.pos, star.position = "WR", "WR"
    star.rating = 80
    assert star.id not in M.protected_ids(league, BEARS)
    rows = M.week_signings(league, WEEK)
    assert [r[2] for r in rows if r[3] == star.id] == [team] and star.team == team
    lines = MF.taken_lines(league, rows, store.words)
    assert len(lines) == 1 and "from your practice squad" in lines[0] and star.name in lines[0] and "Team %d" % team in lines[0]
    # protected: the same league again, the star protected by the player
    league = real_league()
    hurt_family(league, team, "WR", keep=2)
    for p in league.players.values():
        if p.status == P.STATUS and p.pos == "WR":
            p.rating = 41
    star = league.players[star.id]
    star.pos, star.position, star.rating = "WR", "WR", 80
    for p in P.squad(league, BEARS):
        M.set_protected(league, p, False)
    assert M.set_protected(league, star, True) is None and M.protected_ids(league, BEARS) == {star.id}
    M.week_signings(league, WEEK)
    assert star.team == BEARS and star.status == P.STATUS
    league.check()


def test_the_player_team_never_signs_by_itself_and_week_one_and_the_offseason_make_nothing():
    league = real_league()
    hurt_family(league, BEARS, "QB", keep=0)
    rows = M.week_signings(league, WEEK)
    assert all(row[2] != BEARS for row in rows)
    for week in (1, league.regular_weeks + 1):
        assert M.week_signings(league, week) == []
    league.stage = "review"
    assert M.week_signings(league, WEEK) == []


def test_a_full_roster_releases_a_man_whose_family_keeps_its_minimum_and_the_cap_holds():
    league = real_league()
    team = next(t for t in range(1, 33) if t != BEARS and RR.room(league, t) == 0)
    hurt_family(league, team, "S", keep=1)
    used_before = CT.cap_used(league, team)
    rows = [r for r in M.week_signings(league, WEEK) if r[2] == team]
    assert len(rows) == 1 and len(RR.members(league, team)) == D.ROSTER_MAX
    released = [p for p in league.players.values() if p.status == "free" and p.left == league.season and p.team == 0]
    assert released
    assert CT.cap_used(league, team) <= CT.cap_of(league) and used_before >= 0
    league.check()


def test_a_computer_squad_that_lost_a_man_signs_a_free_agent_of_his_family():
    league = real_league()
    team = next(t for t in range(1, 33) if t != BEARS and len(P.squad(league, t)) == P.SIZE)
    man = P.squad(league, team)[-1]
    M.sign_up(league, 1 if team != 1 else 2, man)
    assert len(P.squad(league, team)) == P.SIZE - 1
    joined = M.refill(league, team, man.pos, nfl_surnames.pool(), R.defaults())     # the pool is made when nobody has looked at it yet
    assert joined is not None and joined.pos == man.pos and joined.status == P.STATUS and joined.team == team
    assert len(P.squad(league, team)) == P.SIZE and M.refill(league, team, man.pos) is None       # full again: no more
    league.check()


def test_a_release_never_takes_a_man_of_the_weeks_view_or_of_a_family_with_a_man_hurt():
    league = real_league()
    team = next(t for t in range(1, 33) if t != BEARS and RR.room(league, t) == 0)
    hurt_family(league, team, "S", keep=1, games=1)                          # safeties hurt for this week only: the family is not short, but hurt
    for _ in range(40):
        man = M.release_for(league, team, WEEK, "QB")
        if man is None:
            break
        assert man.place < 0 and man.pos != "S" and man.pos != "QB"
        assert all(I.healthy(league, p.id, WEEK) for p in RR.members(league, team) if p.pos == man.pos)
        assert M.able(league, team, man.pos, WEEK) - 1 >= T.FR_FAMILY_MIN.get(man.pos, 0)
        RR.leave(league, man, "free")
        man.team = 0


def test_a_squad_man_standing_in_this_week_is_never_promoted_by_his_own_team():
    league = real_league()
    team = first_in_turn(league)
    hurt_family(league, team, "LB", keep=1)
    own = [p for p in P.squad(league, team) if p.pos == "LB"]
    assert own
    for p in own:
        league.injuries["stand_ins"].append([team, "LB", p.name, p.rating])
    for p in league.players.values():                                        # nobody else's squad backer is better by the edge
        if p.status == P.STATUS and p.pos == "LB" and p.team != team:
            p.rating = 41
    rows = [r for r in M.week_signings(league, WEEK) if r[2] == team]
    assert all(league.players[r[3]] not in own for r in rows)


# ----- the file -----

def test_format_20_round_trips_and_a_format_19_file_gets_the_staffs_protections():
    league = real_league()
    hurt_family(league, 1, "QB")
    M.week_signings(league, WEEK)
    M.set_protected(league, P.squad(league, BEARS)[0], False)
    data = json.loads(league.to_json())
    assert data["format"] == D.FORMAT == 20 and data["practice"]["signings"] and data["practice"]["protected"] is not None
    again = LeagueRecord.from_json(league.to_json())
    assert again.to_json() == league.to_json()
    data["format"] = 19
    del data["practice"]["protected"], data["practice"]["signings"]
    old = LeagueRecord.from_json(json.dumps(data))
    assert old.practice["protected"] is None and old.practice["signings"] == []


@pytest.mark.parametrize("key,bad", [("protected", [1, 2, 3, 4, 5]), ("protected", [1, 1]), ("protected", ["x"]), ("protected", [10 ** 8]),
                                     ("signings", None), ("signings", [[1, 2, 3]]), ("signings", [[0, 1, 2, 3]]), ("signings", [[2, 40, 1, 3]]),
                                     ("signings", [[2, 1, 2, 10 ** 8]])])
def test_damaged_protections_or_signings_are_damage(key, bad):
    league = real_league()
    data = json.loads(league.to_json())
    data["practice"][key] = bad
    with pytest.raises(LeagueError):
        LeagueRecord.from_json(json.dumps(data))


def test_a_season_end_clears_the_protections_and_the_signings():
    league = real_league()
    hurt_family(league, 1, "QB")
    M.week_signings(league, WEEK)
    M.set_protected(league, P.squad(league, BEARS)[0], False)
    P.dissolve(league)
    assert league.practice == P.empty() and league.practice["protected"] is None and league.practice["signings"] == []


# ----- the menu items -----

def test_the_protect_list_toggles_with_enter_saves_and_refuses_a_fifth():
    league = real_league()
    game, store = franchise(league)
    speech = Speech()
    squad = P.squad(league, BEARS)
    # Enter on the first (protected by the staff): ends it; Down x4, Enter on the fifth: protects him; Down, Enter on the sixth: refused (four already)
    MF.protect_flow(game, speech, Keys(ENTER, DOWN, DOWN, DOWN, DOWN, ENTER, DOWN, ENTER, ESC), store, store.words)
    assert X.text("NXJ-P44").strip() in speech.said[0]                        # the staff's four until he chooses
    assert any(X.text("NXJ-P42", player=squad[0].name).strip() in s for s in speech.said)
    assert any(X.text("NXJ-P41", player=squad[4].name).strip() in s for s in speech.said)
    assert any(X.text("NXJ-P43").strip() in s for s in speech.said)
    assert M.protected_ids(league, BEARS) == {p.id for p in squad[1:5]} and store.saves == 2
    league.check()


def test_the_player_signs_a_man_of_another_teams_squad_with_a_release_and_the_list_names_it():
    league = real_league()
    game, store = franchise(league)
    speech = Speech()
    full = RR.room(league, BEARS) == 0
    keys = [ENTER, ENTER] + ([ENTER] if full else []) + [ENTER]               # the position, the man, (the release), the confirmation
    text = MF.sign_other_flow(game, speech, Keys(*keys), store, store.words)
    assert X.text("NXJ-P46").strip() in speech.said[0]
    row = league.practice["signings"][-1]
    man = league.players[row[3]]
    assert row[2] == BEARS and row[1] != BEARS and man.team == BEARS and man.status == "active" and store.saves == 1
    assert man.name in text and "Team %d" % row[1] in text
    assert len(RR.members(league, BEARS)) <= D.ROSTER_MAX
    league.check()
    speech = Speech()
    MF.league_signings(game, speech, Keys(ESC), store, store.words)
    assert X.text("NXJ-P54").strip() in speech.said[0] and man.name in speech.said[0]


def test_the_items_are_refused_during_a_game_and_the_empty_list_says_so():
    league = real_league()
    game, store = franchise(league, playing=True)
    assert MF.protect_flow(game, Speech(), Keys(), store, store.words) == X.text("NXJ-P10")
    assert MF.sign_other_flow(game, Speech(), Keys(), store, store.words) == X.text("NXJ-P10")
    game, store = franchise(league)
    assert MF.league_signings(game, Speech(), Keys(), store, store.words) == X.text("NXJ-P57")


def test_the_practice_squad_menu_lists_the_new_items_and_the_rules_name_the_signings():
    import inspect
    source = inspect.getsource(PF.practice_menu)
    for text_id in ("NXJ-P37", "NXJ-P45", "NXJ-P53", "NXJ-P58"):
        assert text_id in source
    assert "never to its squad" in X.text("NXJ-P58") and "4 protected" in X.text("NXJ-P58")
    assert "protect squad players" in X.text("NXH-74") and "protect" in X.text("NXH-86")
