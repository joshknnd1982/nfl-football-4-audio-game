"""A tester's three Franchise faults of 2026-10-27, which the owner made his own ("Claude must address all of these"; nfl4 only, rule 0.13). This is inspired
by Jim Kitchen.

1. D-185 "Make sure all free agents are completely accurate": free_agents.txt holds only real unsigned men at their real positions (the 22 of a real
   roster), and a new franchise's free agents keep those positions (more in test_free_agents_and_depth_d169.py and test_free_agents_nxb3.py).
2. D-187 "Add the ability to sign players to the practice squad": the squad takes a free agent within the NFL's rules (16, a 17th place for an
   international man, six veterans, no age or position limit), with a release that makes room when it is full; the add is in the practice squad menu
   and in F9, Franchise, free agents.
3. D-186 "Add ability to reorder your backups": in every position's list of F9, Rules, Depth charts (a quick game or a season, and a franchise), U moves
   a man up one place, N down one, a digit puts him at that place; the order is kept, said in one sentence, and the next game uses it.
"""
import json
import random
from types import SimpleNamespace

import pytest

from nfl4.extras import lineup as L
from nfl4.extras import nfl_surnames
from nfl4.extras import nx_texts as X
from nfl4.extras import quarterbacks as Q
from nfl4.extras import real_names as R
from nfl4.extras import roster_model as RM
from nfl4.extras.franchise import history
from nfl4.extras.franchise import practice as P
from nfl4.extras.franchise import practice_flow as PF
from nfl4.extras.franchise import real_roster as RR
from nfl4.extras.franchise import signings as S
from nfl4.extras.franchise.league import SEASON, LeagueRecord, new_league
from nfl4.game import key_list
from nfl4.game.keys import KEY_DOWN, KEY_ENTER, KEY_ESCAPE, KEY_F1
from nfl4.game.rnd import GameRandom

BEARS = 17
ENTER, ESC, DOWN, F1 = KEY_ENTER, KEY_ESCAPE, KEY_DOWN, KEY_F1


def letter(char):
    return ord(char.upper())


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


def quick_game(depth=""):
    settings = SimpleNamespace(nx_depth=depth, nx_qb_starters="", nx_key_players="")
    saved = []
    game = SimpleNamespace(options=SimpleNamespace(settings=SimpleNamespace(game=settings), save=lambda: saved.append(1)), customization=None,
                           real_names=None, play_engine=None, saved=saved)
    game.real_names = R.defaults()
    Q.apply(game)
    return game


def real_league(seed=3, team=BEARS):
    return new_league(GameRandom(random.Random(seed)), nfl_surnames.pool(), "Kim", team, "20260101-000000", real=R.defaults())


def franchise(league, playing=False):
    store = SimpleNamespace(league=league, saves=0)
    store.words = history.Words(lambda t: "Team %d" % t, lambda: store.league)
    store.save = lambda: setattr(store, "saves", store.saves + 1)
    game = SimpleNamespace(play_engine=object() if playing else None, real_names=R.defaults(), customization=None, options=None)
    return game, store


def in_season(league):
    league.stage, league.gtp = SEASON, 1
    league.prepared = [league.season, league.gtp]
    return league


# ----- 3. the depth chart's moves (D-186) -----

def test_quick_game_u_moves_the_fourth_receiver_to_third_and_the_next_game_uses_it():
    game = quick_game()
    backend = L.QuickBackend(game, BEARS, "Bears")
    before = [m.key for m in backend.men_at("WR")]
    assert len(before) >= 5
    speech = Speech()
    # the list starts on the first starter: Down three times is number 4, U moves him up, Escape leaves
    assert L.choose_flow(speech, Keys(DOWN, DOWN, DOWN, letter("u"), ESC), backend, "WR", 0) is None
    after = [m.key for m in L.QuickBackend(game, BEARS, "Bears").men_at("WR")]
    assert after[2] == before[3] and after[3] == before[2] and sorted(after) == sorted(before)
    spoken = [s for s in speech.said if "moves up" in s]
    name = game.real_names.spoken(before[3])
    assert spoken and spoken[0].startswith(X.text("NXM-R07", player=name, n=3, position="wide receiver", other=game.real_names.spoken(before[2])))
    assert X.text("NXM-R09", player=name) in spoken[0]                          # number 3 of three wide receivers starts
    assert "WR=" in game.options.settings.game.nx_depth and game.saved             # kept in settings.txt
    assert game.real_names.chart(BEARS)[0]["WR"][2] == before[3]                  # the next game's places follow (quarterbacks.apply)


def test_quick_game_a_digit_puts_a_man_at_that_place_and_the_others_move_down_one():
    game = quick_game()
    backend = L.QuickBackend(game, BEARS, "Bears")
    before = [m.key for m in backend.men_at("CB")]
    assert len(before) >= 4
    speech = Speech()
    L.choose_flow(speech, Keys(DOWN, DOWN, DOWN, letter("1"), ESC), backend, "CB", 0)
    after = [m.key for m in backend.men_at("CB")]
    assert after[:4] == [before[3], before[0], before[1], before[2]]
    assert any(s.startswith(X.text("NXM-R07", player=game.real_names.spoken(before[3]), n=1, position="cornerback",
                                   other=game.real_names.spoken(before[0]))) for s in speech.said)


def test_quick_game_n_moves_down_and_the_limits_are_said():
    game = quick_game()
    backend = L.QuickBackend(game, BEARS, "Bears")
    qbs = [m.key for m in backend.men_at("QB")]
    first, second = game.real_names.spoken(qbs[0]), game.real_names.spoken(qbs[1])
    speech = Speech()
    L.choose_flow(speech, Keys(letter("u"), letter("n"), ESC), backend, "QB", 0)
    assert X.text("NXM-R05", player=first, n=1, position="quarterback") in speech.said          # U on the first: already number 1
    down = X.text("NXM-R08", player=first, n=2, position="quarterback", other=second)
    assert down + X.text("NXM-R10", player=first, other=second) in speech.said                  # N: number 2, and the backup starts
    assert [m.key for m in backend.men_at("QB")][:2] == [qbs[1], qbs[0]]
    speech = Speech()
    L.choose_flow(speech, Keys(letter("9"), ESC), backend, "QB", 0)
    assert len(qbs) < 9 and X.text("NXM-R04", position="quarterback", n=len(qbs)) in speech.said
    speech = Speech()
    L.choose_flow(speech, Keys(*([DOWN] * (len(qbs) - 1)), letter("n"), ESC), backend, "QB", 0)
    last = backend.men_at("QB")[-1]
    assert X.text("NXM-R06", player=last.name, position="quarterback", n=len(qbs)) in speech.said


def test_a_man_of_another_position_in_the_list_cannot_be_moved_but_enter_still_makes_him_the_starter():
    game = quick_game()
    backend = L.QuickBackend(game, BEARS, "Bears")
    candidates = backend.candidates("LT")
    other = next(i for i, m in enumerate(candidates) if m.position != "LT")
    speech = Speech()
    L.choose_flow(speech, Keys(*([DOWN] * other), letter("u"), ESC), backend, "LT", 0)
    assert X.text("NXM-R03", player=candidates[other].name, position="left tackle") in speech.said


def test_the_lists_title_and_f1_name_the_move_keys():
    game = quick_game()
    speech = Speech()
    L.choose_flow(speech, Keys(F1, ESC), L.QuickBackend(game, BEARS, "Bears"), "HB", 0)
    assert X.text("NXM-R01").strip() in speech.said[0]
    assert X.text("NXM-R02") in speech.said and "U moves him up" in X.text("NXM-R02") + X.text("NXM-R11")


def test_franchise_moves_are_kept_by_the_staff_saved_and_survive_the_file():
    league = real_league()
    game, store = franchise(league)
    backend = L.FranchiseBackend(game, store)
    before = [m.key for m in backend.men_at("WR")]
    speech = Speech()
    L.choose_flow(speech, Keys(DOWN, DOWN, DOWN, letter("3"), ESC), backend, "WR", 0)
    chart = league.chart[league.team - 1]["WR"]
    assert chart[2] == before[3] and chart[3] == before[2] and store.saves == 1
    assert league.depth["order"]["WR"][:4] == chart[:4]
    RR.refresh_view(league, league.team)                                          # the staff's order (a week, a signing) keeps his order
    assert league.chart[league.team - 1]["WR"][:4] == chart[:4]
    league.check()
    loaded = LeagueRecord.from_json(league.to_json())
    assert loaded.chart[loaded.team - 1]["WR"][:4] == chart[:4]
    starters = [loaded.players[pid].name for pid in loaded.chart[loaded.team - 1]["WR"][:3]]
    assert loaded.players[before[3]].name in starters                              # number 3 of three starts in the franchise's games


def test_franchise_moves_refused_during_a_game_and_a_return_role_can_be_reordered():
    league = real_league()
    game, store = franchise(league, playing=True)
    backend = L.FranchiseBackend(game, store)
    speech = Speech()
    assert L.choose_flow(speech, Keys(letter("n"), ESC), backend, "QB", 0) == X.text("NXI-54")
    game.play_engine = None
    kr = league.chart[league.team - 1]["KR"]
    if len(kr) >= 2:
        RR.move_in_chart(league, "KR", kr[1], 0)
        assert league.chart[league.team - 1]["KR"][0] == kr[1]


def test_the_move_keys_are_in_the_master_key_list():
    row = key_list.BY_ID["depth_move"]
    assert "U" in row.keys and "N" in row.keys and "digit" in row.keys.lower()
    assert "t" not in row.letters                                                 # rule 0.22: T is never another key in a game


# ----- 2. the practice squad (D-187) -----

def test_a_full_real_squad_takes_a_free_agent_after_a_release_and_keeps_the_limits():
    league = in_season(real_league())
    S.ensure_pool(league, nfl_surnames.pool(), R.defaults())
    squad = P.squad(league, BEARS)
    assert len(squad) >= P.SIZE                                                   # the real squads of rosters.txt are full: the tester's report
    agent = next(p for p in S.pool(league) if not P.veteran(p))
    assert P.sign_problem(league, agent) == "the practice squad is full"
    choices = P.release_choices(league, agent)
    assert choices and choices == sorted(choices, key=lambda p: (p.rating, -p.id))
    gone = choices[0]
    P.sign_to_squad(league, agent, release=choices[0])
    assert agent.status == P.STATUS and agent.team == BEARS and gone.status == "free" and gone in S.pool(league)
    assert len(P.squad(league, BEARS)) == len(squad)
    assert agent.position in RM.MADDEN                                            # a real man at his real position
    league.check()


def test_the_veterans_limit_lets_a_veteran_in_only_for_a_veteran():
    league = in_season(real_league())
    S.ensure_pool(league, nfl_surnames.pool(), R.defaults())
    team = next(t for t in range(1, 33) if sum(P.veteran(p) for p in P.squad(league, t)) == P.VETERANS and len(P.squad(league, t)) < P.SIZE + 1)
    league.team = team
    veteran = next(p for p in S.pool(league) if P.veteran(p) and p.age >= 33)  # no age limit in the NFL (D-187)
    members = P.squad(league, team)
    while len(P.squad(league, team)) >= P.SIZE:                                  # room by size, so only the veterans' limit is left
        P.release_from_squad(league, next(p for p in P.squad(league, team) if not P.veteran(p)))
    assert P.sign_problem(league, veteran) == "too many veterans"
    choices = P.release_choices(league, veteran)
    assert choices and all(P.veteran(p) for p in choices)
    P.sign_to_squad(league, veteran, release=choices[0])
    assert sum(P.veteran(p) for p in P.squad(league, team)) == P.VETERANS and members
    league.check()


def test_a_squad_of_seventeen_keeps_its_international_place_on_a_swap_but_sixteen_never_becomes_seventeen():
    league = in_season(real_league())
    S.ensure_pool(league, nfl_surnames.pool(), R.defaults())
    team = next(t for t in range(1, 33) if len(P.squad(league, t)) == P.SIZE + P.INTERNATIONAL)
    league.team = team
    young = [p for p in S.pool(league) if not P.veteran(p)]
    P.sign_to_squad(league, young[0], release=P.release_choices(league, young[0])[0])
    assert len(P.squad(league, team)) == 17
    P.release_from_squad(league, P.squad(league, team)[-1])
    assert len(P.squad(league, team)) == 16 and P.sign_problem(league, young[1]) == "the practice squad is full"


def test_the_add_flow_speaks_the_position_the_man_the_release_and_the_confirmation_then_saves():
    league = in_season(real_league())
    game, store = franchise(league)
    speech = Speech()
    text = PF.add_flow(game, speech, Keys(ENTER, ENTER, ENTER, ENTER), store, store.words)
    assert X.text("NXJ-P29").strip() in speech.said[0]
    joined = [p for p in P.squad(league, BEARS) if p.left == 0 and p.roster_list == "PS" and p.salary == P.salary_of(p)]
    assert text.startswith(" you released ") and "joins it" in text and store.saves == 1
    assert any(X.text("NXJ-P24", n=len(P.squad(league, BEARS)), player="").split(" choose")[0] in s for s in speech.said)
    assert joined
    league.check()


def test_the_practice_squad_menu_has_the_rules_item_and_the_free_agents_menu_the_add():
    import inspect
    from nfl4.extras.franchise import signings_flow
    assert "NXJ-P28" in inspect.getsource(signings_flow.free_agents_menu) and "add_flow" in inspect.getsource(signings_flow.free_agents_menu)
    rules = X.text("NXJ-P33") + X.text("NXJ-P34") + X.text("NXJ-P35")
    assert "16 players" in rules and "17th" in rules and "6 of them may be veterans" in rules and "3 times" in rules and "2 a game" in rules
    assert "NXJ-P32" in inspect.getsource(PF.practice_menu)


def test_the_free_agents_menu_add_is_refused_during_a_game():
    league = in_season(real_league())
    game, store = franchise(league, playing=True)
    assert PF.add_flow(game, Speech(), Keys(), store, store.words) == X.text("NXJ-P10")


# ----- 1. the free agents (D-185) -----

def test_a_new_franchise_has_every_shipped_free_agent_once_at_his_real_position_and_none_on_a_team():
    real = R.defaults()
    league = in_season(real_league())
    S.ensure_pool(league, nfl_surnames.pool(), real)
    pool = {p.name: p for p in S.pool(league)}
    on_teams = {p.name for p in league.players.values() if p.team}
    for _ident, agent in real.free_agents:
        name = real.spoken(agent.name)
        if name in on_teams:
            continue                                                               # (none: the next assert)
        assert name in pool, name
        assert pool[name].position == agent.pos and pool[name].pos == RM.GROUP[agent.pos], name
    assert not {real.spoken(a.name) for _i, a in real.free_agents} & on_teams
    text = R.shipped_text(R.FREE_AGENTS)
    assert "Daxton Hill" not in text and "Ogbonnia Okoronkwo" not in text and "Matt Judon" not in text   # the audit's faults (D-185)
    assert "REDG 34 Matthew Judon" in text and "FB 31 Jakob Johnson" in text and "LG 25 Nash Hutmacher" in text
