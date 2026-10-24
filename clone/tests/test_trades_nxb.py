"""The owner's bug report of 2026-10-24 (D-142, spec/NFL_EXTRA_FEATURES.md section 19), the trades (nfl4 only, rule 0.13):

NX-B5 "It should let you pick the team you want to trade with then the position": F9, Franchise, trades, "ask a team for a player" chooses the team (the
letters find it), then the position, then the player, then whom you give; the league's best of a position stays as the next item.
NX-B4 "The computer can add draft picks the human can not": the proposal's picks menu adds the player's picks and asks for the other team's; the other team
answers by the value rule (`trades.propose`), asking more of his picks when it is short; from the draft to week 1 a trade is player for player, said once.
"""
import copy
import random

import pytest
from drrig import SURNAMES
from frrig import COACH_AND_TEAM, DOWN, ENTER, ESC, F9, UP, WANT_FRANCHISE, franchise_rig, quit_policy, run_until, spoken

from nfl4.extras import nx_texts as X
from nfl4.extras import tuning as T
from nfl4.extras.franchise import contracts as CT
from nfl4.extras.franchise import data as D
from nfl4.extras.franchise import trades as TR
from nfl4.extras.franchise.league import OFFSEASON, SEASON, new_league
from nfl4.game.rnd import GameRandom

TRADES_MENU = [F9] + [DOWN] * 4 + [ENTER] + [DOWN] * 7 + [ENTER]      # F9, Franchise, trades (the 8th item)
ASK_A_TEAM = [DOWN, DOWN, ENTER]                                      # the 3rd item of the trades menu (NX-B5)
PLAYER, OTHER = 1, 2                                                  # the rig's player takes the first team; the team list starts with team 2
TEAM, THEM = 5, 9                                                     # the rules' tests


# ----- the rules: trades.propose (NX-B4) -----

@pytest.fixture()
def tested_values(monkeypatch):
    monkeypatch.setattr(T, "FR_TRADE_MARGIN", 2)                       # the margin of a quarterback is 2 x 12 = 24 (as test_fr_trades.py)
    monkeypatch.setattr(T, "FR_TRADE_PICKS_MAX", 2)
    monkeypatch.setattr(T, "FR_TRADE_PICK_VALUE", (48, 38, 29, 19, 10, 3, 1))
    monkeypatch.setattr(T, "FR_TRADE_PICK_SHARE", {"contend": 70, "middle": 100, "rebuild": 130})


def flat():
    """Every player rated 60, 25 years old, at his market price: two quarterbacks are worth the same, so the other team is short by the margin (24)."""
    league = new_league(GameRandom(random.Random(3)), SURNAMES, "Kim", TEAM, "20260101-000000")
    for p in league.players.values():
        p.rating = p.peak = 60
        p.age, p.potential = 25, "average"
        p.salary, p.years = CT.market_salary(p.pos, 60), 2
    league.sums = [league.strength_sum(t) for t in range(1, D.TEAMS + 1)]
    league.stage, league.gtp = SEASON, 1
    return league


def qbs(league):
    return league.player_at(TEAM, D.PLACES_OF["QB"][0]), league.player_at(THEM, D.PLACES_OF["QB"][0])


RECORDS = [2, 2] * D.TEAMS                                            # every team in the middle


def test_with_no_picks_the_other_team_asks_for_the_cheapest_of_the_players_picks_that_is_enough(tested_values):
    league = flat()
    give, get = qbs(league)
    trade, added = TR.propose(league, TEAM, give, get, (), (), RECORDS, 1)
    assert added == ((3, TEAM),) and trade.picks_a == ((3, TEAM),) and trade.picks_b == ()     # round 3 (29) is the cheapest that makes up 24
    assert TR.ask(league, TEAM, give, get, RECORDS, 1) == trade                                    # the old way to ask is the same rule


def test_a_pick_the_player_adds_is_taken_as_it_is_when_it_is_enough(tested_values):
    league = flat()
    give, get = qbs(league)
    trade, added = TR.propose(league, TEAM, give, get, ((1, TEAM),), (), RECORDS, 1)
    assert added == () and trade == TR.Trade(TEAM, THEM, give.id, get.id, ((1, TEAM),), ())


def test_asking_for_their_pick_makes_them_ask_more_of_his(tested_values):
    league = flat()
    give, get = qbs(league)
    trade, added = TR.propose(league, TEAM, give, get, (), ((1, THEM),), RECORDS, 1)
    # short by 24 + 48 = 72: his round 1 (48), then the cheapest for the 24 left, round 3 (29)
    assert added == ((1, TEAM), (3, TEAM)) and trade.picks_b == ((1, THEM),)
    assert TR.gain(league, trade, THEM, TR.MIDDLE) == 48 + 29 - 48 == 29 >= TR.margin_of("QB")


def test_too_much_asked_is_a_no_and_so_is_a_pick_nobody_owns(tested_values):
    league = flat()
    give, get = qbs(league)
    assert TR.propose(league, TEAM, give, get, ((1, TEAM),), ((1, THEM), (2, THEM)), RECORDS, 1) == (None, ())   # one more of his at most: not enough
    assert TR.propose(league, TEAM, give, get, ((1, THEM),), (), RECORDS, 1) == (None, ())       # he offers a pick that is theirs
    assert TR.propose(league, TEAM, give, get, (), ((1, 3),), RECORDS, 1) == (None, ())          # he asks for a third team's pick
    assert TR.propose(league, TEAM, give, get, ((1, TEAM), (2, TEAM), (3, TEAM)), (), RECORDS, 1) == (None, ())  # three picks: over the limit


def test_after_the_draft_a_proposal_is_player_for_player(tested_values):
    league = flat()
    give, get = qbs(league)
    league.stage, league.stage_no, league.gtp = OFFSEASON, D.STAGE_CUT, T.FR_TRADE_OFFSEASON_WEEK
    assert not TR.picks_open(league)
    assert TR.propose(league, TEAM, give, get, ((1, TEAM),), (), RECORDS, league.gtp) == (None, ())   # no picks can be traded
    trade, added = TR.propose(league, TEAM, give, get, (), (), RECORDS, league.gtp)
    assert trade is None and added == ()                               # short by the margin and no pick to make it up


# ----- the menu: the team first, then the position (NX-B5), and the picks (NX-B4) -----

def run(tmp_path, keys):
    rig = franchise_rig(tmp_path, WANT_FRANCHISE + COACH_AND_TEAM + keys, policy=quit_policy)
    return run_until(rig)


def qb(league, team):
    return league.player_at(team, D.PLACES_OF["QB"][0])


def recording(monkeypatch, answer="as is"):
    """`propose` stood in: notes what the menu sent and answers with that trade ("as is"), with one more pick of the player's ("more") or no (None)."""
    calls = []

    def propose(league, team, give, get, offered, asked, records, week):
        calls.append({"team": team, "other": get.team, "give": give.id, "get": get.id, "offered": tuple(offered), "asked": tuple(asked)})
        if answer is None:
            return None, ()
        extra = ((7, team),) if answer == "more" and (7, team) not in offered else ()
        return TR.Trade(team, get.team, give.id, get.id, tuple(sorted(tuple(offered) + extra)), tuple(asked)), extra
    monkeypatch.setattr(TR, "propose", propose)
    return calls


def test_the_trades_menu_lists_the_team_first_way_then_the_leagues_best(tmp_path):
    rig = run(tmp_path, TRADES_MENU + [DOWN, DOWN, DOWN, ESC, ESC, ESC])
    text = " ".join(spoken(rig))
    assert X.text("NXX-38") in text and X.text("NXX-12") in text
    assert text.index(X.text("NXX-38")) < text.index(X.text("NXX-12"))


def test_the_team_then_the_position_then_the_player_then_whom_you_give_then_send(tmp_path, monkeypatch):
    calls = recording(monkeypatch)
    keys = TRADES_MENU + ASK_A_TEAM + [ENTER, ENTER, ENTER, ENTER, ENTER, ENTER, ESC, ESC, ESC]
    # the first team of the list (team 2), quarterbacks, their best, your quarterback, send the proposal (no picks), yes
    rig = run(tmp_path, keys)
    league = rig.fstore.league
    (call,) = calls
    assert call["other"] == OTHER and call["offered"] == () and call["asked"] == ()
    assert league.players[call["get"]].team == PLAYER and league.players[call["give"]].team == OTHER
    assert league.trades["log"][0][7] == TR.KIND_PLAYER
    text = spoken(rig)
    team = rig.game.league.team(1, OTHER)
    assert any(X.text("NXX-39").strip() in t for t in text)                          # which team
    assert any(X.text("NXX-40", team=team).strip() in t for t in text)               # which position of the team
    assert any(X.text("NXX-41", group=rig.fstore.words.group("QB"), team=team).strip() in t for t in text)
    assert any(X.text("NXX-45", give=league.players[call["give"]].name, get=league.players[call["get"]].name).strip() in t for t in text)


def test_the_letters_find_the_team(tmp_path, monkeypatch):
    calls = recording(monkeypatch)
    rig = franchise_rig(tmp_path, [], policy=quit_policy)
    names = {team: rig.game.league.team((team - 1) // 4 + 1, (team - 1) % 4 + 1) for team in range(2, D.TEAMS + 1)}
    target = next(team for team in range(D.TEAMS, 1, -1) if not any(names[t].lower().startswith(names[team][0].lower()) for t in range(2, team)))
    letters = list(names[target].lower()[:3])
    keys = TRADES_MENU + ASK_A_TEAM + letters + [ENTER, ENTER, ENTER, ENTER, ENTER, ENTER, ESC, ESC, ESC]
    run(tmp_path / "run", keys)
    assert calls and calls[0]["other"] == target


@pytest.fixture()
def events(monkeypatch):
    from nfl4.data import debuglog
    real, seen = debuglog.event, []

    def event(area, what, *rest, **fields):
        seen.append(dict(fields, area=area, what=what))
        return real(area, what, *rest, **fields)
    monkeypatch.setattr(debuglog, "event", event)
    return seen


def test_adding_your_pick_and_asking_for_theirs_goes_into_the_proposal(tmp_path, monkeypatch, events):
    calls = recording(monkeypatch)
    picks = [DOWN, ENTER, ENTER, DOWN, ENTER, ENTER, UP, UP, ENTER]        # add your first pick (round 1), ask for their first (round 1), back up to send
    keys = TRADES_MENU + ASK_A_TEAM + [ENTER, ENTER, ENTER, ENTER] + picks + [ENTER, ESC, ESC, ESC]
    rig = run(tmp_path, keys)
    league = rig.fstore.league
    (call,) = calls
    assert call["offered"] == ((1, PLAYER),) and call["asked"] == ((1, OTHER),)
    assert TR.owner(league, 1, PLAYER) == OTHER and TR.owner(league, 1, OTHER) == PLAYER
    text = spoken(rig)
    assert X.text("NXX-P02", list=X.text("NXX-P04", round=1)) in text                # "you add your round 1 pick."
    assert X.text("NXX-51", list=X.text("NXX-P05", round=1)) in text                 # "you ask for their round 1 pick."
    assert [e["side"] for e in events if e["what"] == "trade_pick_added"] == ["offered", "asked"]       # rule 0.15
    assert any(e["what"] == "trade_proposed" and e["answer"] == "yes" for e in events)


def test_a_pick_taken_out_is_not_sent(tmp_path, monkeypatch):
    calls = recording(monkeypatch)
    picks = [DOWN, ENTER, ENTER, DOWN, DOWN, ENTER, ENTER, UP, UP, UP, ENTER]   # add your round 1, take a pick out (it), back to send
    rig = run(tmp_path, TRADES_MENU + ASK_A_TEAM + [ENTER, ENTER, ENTER, ENTER] + picks + [ENTER, ESC, ESC, ESC])
    (call,) = calls
    assert call["offered"] == () and call["asked"] == ()
    assert X.text("NXX-52", list=X.text("NXX-P04", round=1)) in spoken(rig)


def test_the_limit_of_picks_is_said(tmp_path, monkeypatch):
    recording(monkeypatch)
    add = [ENTER, ENTER]                                                   # on "add one of your picks": open the list, take the first left
    keys = TRADES_MENU + ASK_A_TEAM + [ENTER, ENTER, ENTER, ENTER, DOWN] + add * T.FR_TRADE_PICKS_MAX + [ENTER, ESC, ESC, ESC, ESC, ESC]
    rig = run(tmp_path, keys)
    assert X.text("NXX-54", n=T.FR_TRADE_PICKS_MAX) in spoken(rig)


def test_when_the_other_team_wants_more_it_is_said_before_the_question(tmp_path, monkeypatch):
    recording(monkeypatch, answer="more")
    rig = run(tmp_path, TRADES_MENU + ASK_A_TEAM + [ENTER] * 6 + [ESC, ESC, ESC])
    league = rig.fstore.league
    team = rig.game.league.team(1, OTHER)
    question = next(t for t in spoken(rig) if X.text("NXX-44", team=team) in t)
    assert X.text("NXX-P04", round=7) in question and TR.owner(league, 7, PLAYER) == OTHER


def test_a_no_is_said_and_nothing_moves(tmp_path, monkeypatch):
    recording(monkeypatch, answer=None)
    rig = run(tmp_path, TRADES_MENU + ASK_A_TEAM + [ENTER] * 5 + [ESC, ESC, ESC])
    assert X.text("NXX-23", team=rig.game.league.team(1, OTHER)) in spoken(rig) and rig.fstore.league.trades["log"] == []


def test_the_leagues_best_of_a_position_also_has_the_picks_step(tmp_path, monkeypatch):
    calls = recording(monkeypatch)
    rig = run(tmp_path, TRADES_MENU + [DOWN, DOWN, DOWN, ENTER] + [ENTER, ENTER, ENTER] + [DOWN, ENTER, ENTER, UP, ENTER] + [ENTER, ESC, ESC, ESC])
    (call,) = calls
    assert call["offered"] == ((1, PLAYER),) and rig.fstore.league.trades["log"][0][7] == TR.KIND_PLAYER


def test_the_help_says_how_to_trade(tmp_path):
    text = X.text("NXH-41")
    assert "choose a team" in text and "picks" in text and len(text) <= 200
