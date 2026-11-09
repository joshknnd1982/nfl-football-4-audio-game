"""GitHub issue 8 (Dennisl123, 2026-11-08, on 0.16.20): "After activating someone off injured reserve it can't save the franchise." (nfl4 only, rule 0.13;
D-221). His problem report: Kerby Joseph (PUP list since the franchise began) activated in week 5, then every save refused the whole record with "the
salary of player 1929 is 0". A man the real rosters put on a list has no contract (salary 0: it ran with the list) and the activation brought him to the
53 without one. Now he comes back on the market price (as the roster cut brings list men back), the confirmation says that contract before Enter, and
the save mends any active man with no contract (logged as a warning) instead of refusing the whole franchise.
"""
import logging
import random
from types import SimpleNamespace

import pytest

from nfl4.extras import nfl_surnames
from nfl4.extras import nx_texts as X
from nfl4.extras import real_names as R
from nfl4.extras import tuning as T
from nfl4.extras.franchise import contracts as CT
from nfl4.extras.franchise import history
from nfl4.extras.franchise import injuries as I
from nfl4.extras.franchise import real_roster as RR
from nfl4.extras.franchise import reserve as RV
from nfl4.extras.franchise import reserve_flow as RVF
from nfl4.extras.franchise.files import MemoryFiles
from nfl4.extras.franchise.league import SEASON, new_league, team_ref
from nfl4.extras.franchise.store import FranchiseStore
from nfl4.game.keys import KEY_DOWN, KEY_ENTER, KEY_ESCAPE
from nfl4.game.rnd import GameRandom

WEEK = 1                       # the whole-file check of week 1 needs no played games; the waits are set to 0 below


@pytest.fixture(autouse=True)
def fresh_defaults(monkeypatch):
    R.reset_defaults_cache()
    nfl_surnames._SHIPPED = None
    monkeypatch.setattr(T, "FR_IR_MIN_GAMES", 0)          # the four games and the two before a designation are tested in test_tester_20261106.py;
    monkeypatch.setattr(T, "FR_IR_DESIGNATE_AFTER", 0)    # here the activation itself is tested in a league whose file can be written
    yield
    R.reset_defaults_cache()
    nfl_surnames._SHIPPED = None


def own_man_on_the_list(league):
    """A starting receiver of the player's team, hurt, placed on injured reserve by the player, then healed: a man who has his own contract."""
    man = next(p for p in league.team_men(league.team) if p.position == "WR" and p.place >= 0)
    I.injure(league, man.id, "IJL", 1, 0, WEEK - 1)
    RV.place(league, man, WEEK)
    league.injuries["hurt"] = [row for row in league.injuries["hurt"] if row[0] != man.id]
    return man


def league_for(team, seed=3):
    league = new_league(GameRandom(random.Random(seed)), nfl_surnames.pool(), "Kim", team, "20260101-000000", real=R.defaults())
    league.stage, league.gtp = SEASON, WEEK
    league.prepared = [league.season, league.gtp]
    division, place = team_ref(3 if team != 3 else 4)
    league.schedule = [[division, place, 1] for _ in range(league.regular_weeks)]      # a test's schedule (the whole-file check needs one)
    return league


def listed(league, team, lists):
    return [p for p in RV.on_list(league, team) if p.roster_list in lists and I.healthy(league, p.id, WEEK)]


def team_with(lists):
    """A team whose real roster has a healthy man on one of `lists` when the franchise begins, and that man (both from the shipped rosters)."""
    probe = league_for(1)
    for team in range(1, 33):
        if listed(probe, team, lists):
            league = league_for(team)
            return league, listed(league, team, lists)[0]
    pytest.skip("no team of the shipped rosters has a man on %s" % (lists,))


def bring_back(league, man):
    """Designate him when the list needs it, then activate him (releasing the lowest rated man when the 53 is full). Returns the man released or None."""
    if man.roster_list in RV.ON_IR:
        assert RV.designate_problem(league, man, WEEK) is None
        RV.designate(league, man, WEEK)
    release = RV.releasable(league, man, WEEK)[0] if RR.room(league, league.team) <= 0 else None
    assert RV.activate_problem(league, man, WEEK, release) is None
    RV.activate(league, man, WEEK, release)
    return release


def through_store(league):
    files = MemoryFiles()
    store = FranchiseStore(files)
    store.strict = True                         # a record that is not whole raises here instead of being logged
    store.league = league
    assert store.save()
    again = FranchiseStore(files)
    again.strict = True
    again.open(True)
    return again.league


def test_the_real_lists_begin_with_no_contract():
    """The cause: every man the real rosters put on a list has salary 0 when the franchise begins (his contract ran with the list)."""
    league = league_for(1)
    men = [p for p in league.players.values() if p.status == "list" and 1 <= p.team <= 32]
    assert men and all(p.salary == 0 and p.years == 0 for p in men)
    assert all(RV.new_contract(p) == CT.market_contract(p) for p in men)


@pytest.mark.parametrize("lists", [RV.OTHER_LISTS, RV.ON_IR], ids=["pup_or_nfi", "injured_reserve"])
def test_a_man_who_began_on_a_real_list_comes_back_on_a_contract_and_the_franchise_saves(lists):
    league, man = team_with(lists)
    assert man.salary == 0
    bring_back(league, man)
    assert man.status == "active" and (man.salary, man.years) == CT.market_contract(man)
    assert T.FR_MIN_SALARY <= man.salary <= T.FR_MAX_SALARY and man.years >= 1
    league.check()                                                    # the tester's error: "the salary of player 1929 is 0"
    again = through_store(league)
    back = again.players[man.id]
    assert (back.status, back.salary, back.years) == ("active", man.salary, man.years)


def test_a_man_the_player_placed_keeps_his_own_contract():
    league, _man = team_with(RV.OTHER_LISTS + RV.ON_IR)
    man = own_man_on_the_list(league)
    own = (man.salary, man.years)
    assert own[0] >= T.FR_MIN_SALARY and RV.new_contract(man) is None
    bring_back(league, man)
    assert (man.salary, man.years) == own
    league.check()


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
        return self.answers.pop(0) if self.answers else KEY_ESCAPE


def test_the_confirmation_says_the_new_contract_and_the_franchise_is_written():
    """The menu as the tester used it: F9, Franchise, injured reserve, the lists, his man, Enter (and the release), Enter. The real store writes."""
    league, man = team_with(RV.OTHER_LISTS)
    files = MemoryFiles()
    store = FranchiseStore(files)
    store.strict = True
    store.league = league
    words = history.Words(lambda t: "Team %d" % t, lambda: store.league)
    index = RV.on_list(league).index(man)
    full = RR.room(league, league.team) <= 0
    keys = Keys(KEY_DOWN, KEY_ENTER, *([KEY_DOWN] * index), KEY_ENTER, *([KEY_ENTER] if full else []), KEY_ENTER)
    speech = Speech()
    game = SimpleNamespace(play_engine=None)
    RVF.reserve_menu(game, speech, keys, store, words)
    contract = words.contract_of(*CT.market_contract(man))
    told = X.text("NXI-R43", player=man.name, contract=contract)
    asked = [t for t in speech.said if t.startswith(told)]
    assert asked, speech.said[-6:]
    assert "Enter" in asked[0]                                       # said before the Enter that activates him
    assert man.status == "active" and man.salary >= T.FR_MIN_SALARY
    again = FranchiseStore(files)
    again.strict = True
    again.open(True)
    assert again.league.players[man.id].status == "active"            # the activation is in league.sav
    done = X.text("NXI-R20" if full else "NXI-R19", player=man.name, give="", get=man.name).strip()
    assert any(man.name in t and "back on your active roster" in t for t in speech.said), done


def test_no_contract_sentence_for_a_man_who_has_his_own():
    league, _man = team_with(RV.OTHER_LISTS + RV.ON_IR)
    man = own_man_on_the_list(league)
    RV.designate(league, man, WEEK)
    store = SimpleNamespace(league=league, save=lambda: True)
    words = history.Words(lambda t: "Team %d" % t, lambda: store.league)
    index = RV.on_list(league).index(man)
    full = RR.room(league, league.team) <= 0
    speech = Speech()
    keys = Keys(KEY_DOWN, KEY_ENTER, *([KEY_DOWN] * index), KEY_ENTER, *([KEY_ENTER] if full else []), KEY_ENTER)
    RVF.reserve_menu(SimpleNamespace(play_engine=None), speech, keys, store, words)
    assert man.status == "active"
    assert not any("comes back on a new contract" in t for t in speech.said)


def events(monkeypatch):
    """The debug log's events of the test (rule 0.15), as (name, fields)."""
    from nfl4.data import debuglog
    seen = []
    monkeypatch.setattr(debuglog, "event", lambda component, name, level=logging.DEBUG, /, **fields: seen.append((name, level, fields)))
    return seen


def test_the_save_mends_an_active_man_with_no_contract_and_logs_it(monkeypatch):
    """The safety net: a man brought back by any path without a contract no longer makes the whole franchise unsaveable."""
    league, man = team_with(RV.OTHER_LISTS + RV.ON_IR)
    man.status, man.roster_list = "active", ""                       # a path that forgot the contract (the 0.16.20 activation did this)
    RR.join(league, league.team, man)
    assert man.salary == 0
    files = MemoryFiles()
    store = FranchiseStore(files)
    store.strict = True
    store.league = league
    seen = events(monkeypatch)
    assert store.save()
    assert (man.salary, man.years) == CT.market_contract(man)
    mended = [fields for name, level, fields in seen if name == "contract_mended"]
    assert mended and man.id in mended[0]["players"] and [level for name, level, _ in seen if name == "contract_mended"] == [logging.WARNING]
    again = FranchiseStore(files)
    again.strict = True
    again.open(True)
    assert again.league.players[man.id].salary == man.salary


def test_a_whole_record_is_not_touched_by_the_mend(monkeypatch):
    league = league_for(1)
    before = {p.id: (p.salary, p.years) for p in league.players.values()}
    seen = events(monkeypatch)
    through_store(league)
    assert {p.id: (p.salary, p.years) for p in league.players.values()} == before
    assert not any(name == "contract_mended" for name, _level, _fields in seen)
