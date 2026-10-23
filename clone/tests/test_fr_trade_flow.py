"""Trades on the program rig (nfl4 only, rule 0.13; NFL_FRANCHISE_DESIGN 17 SX.8j, D-070): an offer in the week's to-do list (accept, decline, later and the
kick-off, the staff setting), the computer teams' trades in the news, F9's trades item, and the draft that speaks the picks a trade moved. The rules are
test_fr_trades.py. Where a test needs one particular offer it puts it in place of the search's answer (`offer_in_week`), so the flow is tested whatever the
rig's league happens to hold; the search itself is tested on strict leagues in test_fr_trades.py.
"""
import pytest
from drrig import at_stage, draft_league, offseason_rig
from frrig import (COACH_AND_TEAM, DOWN, ENTER, ESC, F9, WANT_FRANCHISE, franchise_rig, quit_policy, run_until, spoken)

from nfl4.extras import nx_texts as X
from nfl4.extras import tuning as T
from nfl4.extras.franchise import data as D
from nfl4.extras.franchise import trade_flow
from nfl4.extras.franchise import trades as TR
from nfl4.extras.franchise.league import LeagueRecord
from nfl4.extras.franchise.store import FranchiseStore

GAME = [ENTER, ENTER, ENTER]                                  # a regular week: the menu's play game, the results, the standings
TRADES_MENU = [F9] + [DOWN] * 4 + [ENTER] + [DOWN] * 7 + [ENTER]      # F9, Franchise, trades (the 8th item)
PLAYER, OTHER = 1, 2                                          # the rig's player takes the first team


def qb(league, team):
    return league.player_at(team, D.PLACES_OF["QB"][0])


def offer_in_week(monkeypatch, week=2, teams=(PLAYER, OTHER), picks_a=((3, PLAYER),), seen=None):
    """The search's answer in `week` is one trade of the two teams' quarterbacks, the first team adding `picks_a`; nothing in the other weeks. The
    records the search was given are noted in `seen`."""
    def search(league, week_no, records):
        if seen is not None:
            seen.append((week_no, list(records), list(league.records)))
        if week_no != week:
            return []
        a, b = teams
        return [TR.Trade(a, b, qb(league, a).id, qb(league, b).id, tuple(picks_a), ())]
    monkeypatch.setattr(TR, "search", search)
    monkeypatch.setattr(T, "FR_EXTRA_WORK_WEEKS", ())          # no extra-work item: the trade is the week's only item


def watch_saves(monkeypatch, rig_box):
    """Every save is noted as (lines spoken so far, trades in the log)."""
    real = FranchiseStore.save
    rows = []

    def save(self):
        ok = real(self)
        if self.league is not None and rig_box:
            rows.append((len(rig_box[0].said), len(self.league.trades["log"])))
        return ok
    monkeypatch.setattr(FranchiseStore, "save", save)
    return rows


def run(tmp_path, keys, setup=None, **kwargs):
    rig = franchise_rig(tmp_path, WANT_FRANCHISE + COACH_AND_TEAM + keys, policy=quit_policy, **kwargs)
    if setup is not None:
        setup(rig)
    return run_until(rig)


def league_of(rig):
    return rig.fstore.league


def started_quarterbacks(tmp_path):
    """The two quarterbacks of the rig's league as it is made (seed 1), before any trade."""
    rig = run(tmp_path / "plain", [])
    league = league_of(rig)
    return qb(league, PLAYER).id, qb(league, OTHER).id


# ----- an offer in the to-do list -----

def test_an_offer_is_asked_in_the_weeks_list_and_its_first_answer_makes_the_trade_written_before_it_is_told(tmp_path, monkeypatch):
    mine, theirs = started_quarterbacks(tmp_path)
    offer_in_week(monkeypatch)
    box = []
    saves = watch_saves(monkeypatch, box)
    rig = franchise_rig(tmp_path / "run", WANT_FRANCHISE + COACH_AND_TEAM + GAME + [ENTER], policy=quit_policy)
    box.append(rig)
    run_until(rig)
    league = league_of(rig)
    text = spoken(rig)
    assert X.text("NXD-02", coach="kim") in text and X.text("NXD-05", n=1) in text
    offer = next(t for t in text if t.startswith(" a trade offer from the "))
    assert X.text("NXX-A01") in " ".join(text) and " you add your round 3 pick. " in offer
    assert qb(league, PLAYER).id == theirs and qb(league, OTHER).id == mine
    assert league.trades["log"][0][7] == TR.KIND_OFFER and TR.owner(league, 3, PLAYER) == OTHER
    made = X.text("NXX-02", get=league.players[theirs].name, give=league.players[mine].name, team=rig.game.league.team(1, 2))
    assert made in text
    told_at = [i for i, (t, _, _) in enumerate(rig.said) if t == made][0]
    assert any(count == 1 and lines <= told_at for lines, count in saves)  # a save with the trade came before the sentence
    assert league.todo == []


def test_the_second_answer_declines_and_nothing_is_traded(tmp_path, monkeypatch):
    mine, _theirs = started_quarterbacks(tmp_path)
    offer_in_week(monkeypatch)
    rig = run(tmp_path / "run", GAME + [DOWN, ENTER])
    league = league_of(rig)
    assert qb(league, PLAYER).id == mine and league.trades == {"picks": [], "log": []} and league.todo == []
    assert X.text("NXX-04", team=rig.game.league.team(1, 2)) in spoken(rig)


def test_an_offer_left_for_later_is_declined_at_the_kick_off_nothing_is_decided_for_the_player(tmp_path, monkeypatch):
    mine, _theirs = started_quarterbacks(tmp_path)
    offer_in_week(monkeypatch)
    later = [DOWN, DOWN, ENTER]
    rig = run(tmp_path / "run", GAME + later + [ENTER] + later)           # later, play game (asked again), later again: the game starts
    league = league_of(rig)
    text = spoken(rig)
    assert X.text("NXD-06", n=1) in text and X.text("NXD-30") in text
    assert qb(league, PLAYER).id == mine and league.trades["log"] == [] and league.todo == []


def test_with_the_staff_setting_on_the_staff_accepts_and_says_the_trade(tmp_path, monkeypatch):
    mine, theirs = started_quarterbacks(tmp_path)
    offer_in_week(monkeypatch)

    def auto(rig):
        rig.game.options.settings.game.nx_fr_auto = True
    rig = run(tmp_path / "run", GAME, setup=auto)
    league = league_of(rig)
    text = spoken(rig)
    assert X.text("NXD-04", n=1) in text and not any(t.startswith(" a trade offer from the ") for t in text)
    picks = X.text("NXX-P02", list=X.text("NXX-P04", round=3))                  # the staff tells the picks he has not heard: "you add your round 3 pick."
    assert X.text("NXX-05", team=rig.game.league.team(1, 2), get=league.players[theirs].name, give=league.players[mine].name, picks=picks) in text
    assert qb(league, PLAYER).id == theirs and league.trades["log"][0][7] == TR.KIND_OFFER


def test_an_offer_that_can_no_longer_be_made_is_called_off(tmp_path, monkeypatch):
    mine, _theirs = started_quarterbacks(tmp_path)
    offer_in_week(monkeypatch, picks_a=((3, OTHER),))                    # a pick the player's team does not own
    rig = run(tmp_path / "run", GAME + [ENTER])
    league = league_of(rig)
    assert X.text("NXX-03") in spoken(rig) and qb(league, PLAYER).id == mine and league.trades["log"] == []


def test_the_weeks_trades_are_looked_for_with_the_records_of_the_weeks_played(tmp_path, monkeypatch):
    seen = []
    offer_in_week(monkeypatch, week=99, seen=seen)
    from nfl4.extras.franchise import injuries
    monkeypatch.setattr(injuries, "to_ask", lambda league, week: [])         # SX.8k: no injury question takes a key of the script
    run(tmp_path, GAME + GAME + GAME)
    assert [week for week, _r, _l in seen] == [1, 2, 3, 4]
    for week, given, held in seen:
        assert given == held and sum(given) == 32 * (week - 1)             # the league's own records: every team has played week - 1 games


def test_two_other_teams_trade_and_the_news_tells_it_within_the_weeks_lines(tmp_path, monkeypatch):
    offer_in_week(monkeypatch, teams=(3, 4), picks_a=())
    rig = run(tmp_path, GAME + [ENTER])
    league = league_of(rig)
    assert league.trades["log"][0][7] == TR.KIND_COMPUTER and league.todo == []
    lines = [e for e in league.news if e["week"] == 1]
    assert [e["pool"] for e in lines].count("NWX") == 1 and len(lines) <= T.FR_NEWS_MAX
    assert lines[[e["pool"] for e in lines].index("NWX")]["told"] == 1


# ----- F9, franchise, trades -----

def test_the_franchise_menu_has_trades_and_its_draft_picks_and_season_lists(tmp_path):
    rig = run(tmp_path, TRADES_MENU + [DOWN, DOWN, DOWN, ENTER, ESC, DOWN, ENTER, ESC, ESC, ESC, ESC])
    text = spoken(rig)
    assert any(X.text("NXX-28", n=T.FR_TRADE_LAST_WEEK).strip() in t for t in text)     # the menu's title says the deadline's week
    assert any(X.text("NXX-P04", round=1) in t for t in text)                # your draft picks: your round 1 pick ...
    assert X.text("NXG-18") in text                                       # trades this season: nothing yet


def test_offering_a_player_hears_the_offers_and_enter_makes_the_chosen_trade(tmp_path, monkeypatch):
    mine, theirs = started_quarterbacks(tmp_path)

    def offers(league, team, player, records, week):
        return [(TR.Trade(team, OTHER, player.id, qb(league, OTHER).id, (), ((4, OTHER),)), 12)]
    monkeypatch.setattr(TR, "block_offers", offers)
    rig = run(tmp_path / "run", TRADES_MENU + [DOWN, ENTER, ENTER, ENTER, ENTER, ENTER, ESC, ESC, ESC])   # offer a player, quarterback, him, the offer, yes
    league = league_of(rig)
    assert qb(league, PLAYER).id == theirs and TR.owner(league, 4, OTHER) == PLAYER
    assert league.trades["log"][0][7] == TR.KIND_PLAYER
    other = rig.game.league.team(1, 2)
    picks = X.text("NXX-P01", team=other, list=X.text("NXX-P05", round=4))                     # "the <team> add their round 4 pick."
    assert X.text("NXX-22", team=other, get=league.players[theirs].name, give=league.players[mine].name, picks=picks) in spoken(rig)
    saved = LeagueRecord.from_json(rig.files.data["league.sav"].decode("utf-8"))
    assert saved.trades == league.trades                                  # written before it was told


def test_offering_a_player_nobody_wants_says_so(tmp_path, monkeypatch):
    monkeypatch.setattr(TR, "block_offers", lambda *a: [])
    rig = run(tmp_path, TRADES_MENU + [DOWN, ENTER, ENTER, ENTER, ESC, ESC, ESC])
    league = league_of(rig)
    assert X.text("NXX-17", give=qb(league, PLAYER).name) in spoken(rig) and league.trades["log"] == []


def test_escape_at_the_confirmation_keeps_the_player(tmp_path, monkeypatch):
    mine, _theirs = started_quarterbacks(tmp_path)

    def offers(league, team, player, records, week):
        return [(TR.Trade(team, OTHER, player.id, qb(league, OTHER).id), 5)]
    monkeypatch.setattr(TR, "block_offers", offers)
    rig = run(tmp_path / "run", TRADES_MENU + [DOWN, ENTER, ENTER, ENTER, ENTER, ESC, ESC, ESC, ESC])
    league = league_of(rig)
    assert qb(league, PLAYER).id == mine and league.trades["log"] == []
    assert X.text("NXX-04", team=rig.game.league.team(1, 2)) in spoken(rig)


def test_asking_for_a_player_hears_the_other_teams_answer_and_enter_makes_it(tmp_path, monkeypatch):
    calls = []

    def ask(league, team, give, get, records, week):
        calls.append((give.id, get.id))
        return TR.Trade(team, get.team, give.id, get.id, ((2, team),), ())
    monkeypatch.setattr(TR, "ask", ask)
    rig = run(tmp_path, TRADES_MENU + [DOWN, DOWN, ENTER, ENTER, ENTER, ENTER, ENTER, ESC, ESC, ESC])     # ask, quarterback, the best one, give mine, yes
    league = league_of(rig)
    (give, get), = calls
    assert qb(league, PLAYER).id == get and league.players[give].team != PLAYER
    best = max((p for p in league.players.values() if p.status == "active" and p.pos == "QB" and p.id != give), key=lambda p: (p.rating, -p.id))
    assert get == best.id or league.players[get].rating == best.rating
    assert TR.owner(league, 2, PLAYER) != PLAYER and league.trades["log"][0][7] == TR.KIND_PLAYER


def test_asking_for_a_player_the_other_team_will_not_give(tmp_path, monkeypatch):
    monkeypatch.setattr(TR, "ask", lambda *a: None)
    rig = run(tmp_path, TRADES_MENU + [DOWN, DOWN, ENTER, ENTER, ENTER, ENTER, ESC, ESC, ESC])
    league = league_of(rig)
    assert any(t.endswith(" say no to that trade. ") for t in spoken(rig)) and league.trades["log"] == []


def test_trades_are_closed_after_the_deadline(tmp_path, monkeypatch):
    monkeypatch.setattr(T, "FR_TRADE_LAST_WEEK", 0)
    rig = run(tmp_path, TRADES_MENU + [DOWN, ENTER, DOWN, ENTER, ESC, ESC, ESC])
    assert spoken(rig).count(X.text("NXX-15", n=0)) >= 2                             # the deadline's week is said


def test_trades_are_closed_inside_a_game():
    class Game:
        play_engine = object()

    class League:
        stage, gtp, calendar = "season", 3, None
    assert trade_flow.closed_reason(Game(), League()) == X.text("NXX-16")
    Game.play_engine = None
    assert trade_flow.closed_reason(Game(), League()) is None
    League.gtp = T.FR_TRADE_LAST_WEEK + 1
    assert trade_flow.closed_reason(Game(), League()) == X.text("NXX-15", n=T.FR_TRADE_LAST_WEEK)


def test_the_season_list_names_a_trade_of_the_season(tmp_path, monkeypatch):
    offer_in_week(monkeypatch, teams=(3, 4), picks_a=((5, 3),))
    rig = run(tmp_path, GAME + [ENTER] + TRADES_MENU + [DOWN, DOWN, DOWN, DOWN, ENTER, ESC, ESC, ESC, ESC])
    league = league_of(rig)
    row = league.trades["log"][0]
    line = trade_flow.log_line(league_words(rig), league, row)
    assert line.startswith(" week 2: the ") and any(line.strip() in t for t in spoken(rig))      # (a list opens with its title and its first line)


def league_words(rig):
    return rig.fstore.words


# ----- the draft speaks the picks a trade moved -----

def test_the_draft_says_the_players_picks_when_a_trade_moved_one(tmp_path):
    def mutate(league):
        league.trades["picks"] = [[1, 5, 9], [2, 9, 5]]                  # the player (team 5) traded his first-round pick and got team 9's second
    league = draft_league(team=5, mutate=mutate)
    rig = offseason_rig(tmp_path, league, until=at_stage(D.STAGE_CUT), picks_told="mine")
    record = rig.fstore.league
    draft = record.draft
    order = draft["order"]
    assert draft["owners"][order.index(5)] == 9 and draft["owners"][D.TEAMS + order.index(9)] == 5
    picks = [(i // D.TEAMS + 1, i % D.TEAMS + 1) for i, owner in enumerate(draft["owners"]) if owner == 5]
    expected = X.text("NXK-14", list=", ".join(X.text("NXK-15", round=r, pick=k) for r, k in picks))
    assert expected in spoken(rig) and X.text("NXK-01", n=order.index(5) + 1) not in spoken(rig)
    assert [row[0] for row in draft["picks"]] == draft["owners"] and record.trades["picks"] == []
    assert len(record.waiting_rookies(5)) == 7 and len(record.waiting_rookies(9)) == 7


def test_the_draft_says_the_one_line_when_no_pick_moved(tmp_path):
    league = draft_league(team=5)
    rig = offseason_rig(tmp_path, league, until=at_stage(D.STAGE_DRAFT, pick=1), picks_told="mine")
    order = rig.fstore.league.draft["order"]
    assert X.text("NXK-01", n=order.index(5) + 1) in spoken(rig)


@pytest.mark.parametrize("staff", [False, True])
def test_the_new_season_drops_the_seasons_trades(tmp_path, staff):
    def mutate(league):
        league.trades["log"] = [[5, 3, 4, league.player_at(3, 0).id, league.player_at(4, 0).id, [], [], 0]]
    league = draft_league(team=5, stage_no=D.STAGE_NEW_SEASON, mutate=mutate)
    rig = offseason_rig(tmp_path, league, auto=staff)
    assert rig.fstore.league.trades == {"picks": [], "log": []}


# ----- the SX.8j review's missing cases -----

def test_the_weekly_preparation_makes_the_real_searchs_trades_and_offers_the_players_one(monkeypatch):
    """`weekly.prepare` with the real search (no stand-in): two pairs of a contender with a young quarterback and a rebuilder with a veteran; the pair without the
    player's team is traded at once and told in the news, the pair with it is an offer in his list; nothing of his team changes until he answers."""
    import random
    from types import SimpleNamespace
    from drrig import SURNAMES
    from nfl4.extras.franchise import contracts as CT
    from nfl4.extras.franchise import history, weekly
    from nfl4.extras.franchise.league import SEASON, new_league
    from nfl4.game.rnd import GameRandom
    monkeypatch.setattr(T, "FR_TRADE_WEEK_MAX", 2)
    monkeypatch.setattr(T, "FR_INJ_PRACTICE", (T.FR_INJ_PRACTICE[0], 0))       # SX.8k: the week's injury draws are made but hurt nobody (a hurt player is not traded)
    monkeypatch.setattr(T, "FR_INJ_GAME", (T.FR_INJ_GAME[0], 0))
    league = new_league(GameRandom(random.Random(3)), SURNAMES, "Kim", 9, "20260101-000000")
    for player in league.players.values():                                 # no veteran anywhere but the two below
        player.rating = player.peak = 60
        player.age, player.potential = 25, "average"
        player.salary, player.years = CT.market_salary(player.pos, 60), 2
    records = [2, 2] * D.TEAMS
    for contender, rebuilder in ((4, 9), (14, 15)):                        # the player's team is 9, a rebuilder
        young, veteran = qb(league, contender), qb(league, rebuilder)
        young.rating, young.age, young.potential, young.salary = 72, 23, "high", CT.market_salary("QB", 72)
        veteran.rating, veteran.peak, veteran.age, veteran.salary = 86, 86, 30, CT.market_salary("QB", 86)
        records[2 * contender - 2:2 * contender] = [3, 1]
        records[2 * rebuilder - 2:2 * rebuilder] = [1, 3]
    league.sums = [league.strength_sum(team) for team in range(1, D.TEAMS + 1)]
    league.stage, league.gtp, league.records = SEASON, 5, records
    mine = qb(league, 9).id
    saves = []
    store = SimpleNamespace(words=history.Words(lambda team: "Team%d" % team), save=lambda: saves.append(len(league.trades["log"])))
    game = SimpleNamespace(news_pools=None, rnd=GameRandom(random.Random(1)), playbook_table=None,
                           options=SimpleNamespace(settings=SimpleNamespace(game=SimpleNamespace(nx_offense_playbook="classic", nx_defense_playbook="classic"))))
    weekly.prepare(SimpleNamespace(g=game, store=store, season=SimpleNamespace(tn3=1, tn4=2, on_bye=False)), league, 5)
    (row,) = league.trades["log"]                                           # the computer trade: a contender (4 or 14) with team 15
    assert row[7] == TR.KIND_COMPUTER and row[1] in (4, 14) and row[2] == 15 and qb(league, row[1]).rating == 86 and qb(league, 9).id == mine
    (item,) = [item for item in league.todo if item["kind"] == D.TODO_TRADE]   # the other contender's offer to the player's team, waiting
    other = 18 - row[1]
    assert item["trade"][:4] == [other, 9, qb(league, other).id, mine] and item["week"] == 5 and qb(league, other).rating == 72
    assert [e["pool"] for e in league.news].count("NWX") == 1 and saves == [1]


def test_an_offer_left_for_later_is_taken_by_the_staff_at_the_kick_off_when_the_setting_was_turned_on_in_f9(tmp_path, monkeypatch):
    mine, theirs = started_quarterbacks(tmp_path)
    offer_in_week(monkeypatch)
    later = [DOWN, DOWN, ENTER]
    turn_on = [F9] + [DOWN] * 4 + [ENTER] + [DOWN] * 11 + [ENTER, ENTER, ESC, ESC, ESC]       # F9, Franchise, settings (11th since SX.8l), the staff item: on   # D-136: practice squad is the 10th item
    rig = run(tmp_path / "run", GAME + later + turn_on + [ENTER])
    league = league_of(rig)
    assert rig.game.options.settings.game.nx_fr_auto is True and qb(league, PLAYER).id == theirs
    assert league.trades["log"][0][7] == TR.KIND_OFFER and X.text("NXD-30") not in spoken(rig)


def test_an_offer_whose_player_was_traded_in_f9_meanwhile_is_called_off(tmp_path, monkeypatch):
    mine, _theirs = started_quarterbacks(tmp_path)
    offer_in_week(monkeypatch)

    def offers(league, team, player, records, week):
        return [(TR.Trade(team, 3, player.id, qb(league, 3).id), 7)]
    monkeypatch.setattr(TR, "block_offers", offers)
    later = [DOWN, DOWN, ENTER]
    block = TRADES_MENU + [DOWN, ENTER, ENTER, ENTER, ENTER, ENTER, ESC, ESC, ESC]          # F9: his quarterback to team 3
    rig = run(tmp_path / "run", GAME + later + block + [ENTER, ENTER])                      # play game: the offer asked again, accept
    league = league_of(rig)
    assert league.players[mine].team == 3 and [row[7] for row in league.trades["log"]] == [TR.KIND_PLAYER]
    assert X.text("NXX-03") in spoken(rig) and league.todo == []
