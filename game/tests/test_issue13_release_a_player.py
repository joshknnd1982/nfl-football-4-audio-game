"""GitHub issue 13 (Dennisl123 on 0.16.24, D-226): "Currently in franchise mode there is currently no way to release someone unless you are planning to
sign someone this needs updated." (nfl4 only, rule 0.13). This is inspired by Jim Kitchen.

A man of the player's 53 is released with no signing: "release him", the last of a man's items in F9, Franchise, your roster (a practice squad man is
released from the squad there too), and "release a player", the fourth item of F9, Franchise, free agents. In the season (the regular weeks and the
play-offs) before the kick-off; not a hurt man, not below a family minimum, not over the cap; one confirmation with his contract, his dead money and the
cap room after; made and written, then told.
"""
import pytest

from programrig import DOWN, ENTER, ESC
from test_lineup_sr6 import Keys, Speech, franchise, real_league

from nfl4.extras import nx_texts as X
from nfl4.extras import real_names as R
from nfl4.extras import tuning as T
from nfl4.extras.franchise import contracts as CT
from nfl4.extras.franchise import injuries
from nfl4.extras.franchise import real_roster
from nfl4.extras.franchise import roster_flow
from nfl4.extras.franchise import signings as S
from nfl4.extras.franchise import signings_flow as SF
from nfl4.game.keys import KEY_END as END


@pytest.fixture(autouse=True)
def fresh_defaults():
    R.reset_defaults_cache()
    yield
    R.reset_defaults_cache()


def ready_league():
    """A new franchise in week 1 of the regular season, its week prepared (the main menu before the game)."""
    league = real_league()
    league.prepared = [league.season, league.gtp]
    return league


def chart_of(league, key):
    return [league.players[pid] for pid in league.chart[league.team - 1].get(key, ())]


def section_of(game, store, key):
    return next(s for s in roster_flow.sections_of(game, store) if s.key == key)


def spare_position(league):
    """A position of the 22 whose family the team holds more of than its minimum (the Bears of this league: the defensive line), with two men or more."""
    from nfl4.extras import roster_model as RM
    have = real_roster.counts_by_group(real_roster.members(league, league.team))
    return next(key for key in RM.MADDEN if have.get(RM.GROUP[key], 0) > T.FR_FAMILY_MIN.get(RM.GROUP[key], 0) and len(chart_of(league, key)) >= 2)


def lowest_releasable(league):
    """A man of a family with room above its minimum: the last of such a position's chart."""
    return chart_of(league, spare_position(league))[-1]


# ----- the roster: "release him" is the last item of a man -----

def test_release_him_is_the_last_item_of_a_man_of_the_53_and_the_others_keep_their_places(monkeypatch):
    from nfl4.game import spoken_menu
    seen = []
    real = spoken_menu.SpokenMenu.__init__

    def spy(self, speech, keys, title, items, *args, **kwargs):
        seen.append([item.label() for item in items])
        real(self, speech, keys, title, items, *args, **kwargs)
    monkeypatch.setattr(spoken_menu.SpokenMenu, "__init__", spy)
    league = ready_league()
    game, store = franchise(league)
    qb = chart_of(league, "QB")[1]
    roster_flow.man_items(game, Speech(), Keys(ESC), store, section_of(game, store, "QB"), qb)
    labels = seen[-1]
    assert labels[-1] == X.text("NXM-L93").strip() and labels[-2] == X.text("NXM-L29").strip() and labels[-3] == X.text("NXM-L92").strip()


def test_release_him_from_the_roster_releases_the_man_with_one_confirmation():
    league = ready_league()
    game, store = franchise(league)
    speech = Speech()
    man = lowest_releasable(league)
    team = league.team
    count = real_roster.roster_count(league, team)
    dead = CT.dead_money(man)
    dead_before = league.dead[team - 1]
    salary = man.salary
    room_after = CT.cap_of(league) - (CT.cap_used(league, team) - salary + dead)
    words = store.words
    asked = X.text("NXJ-S22", player=man.name, contract=words.contract(man), dead=words.amount(dead), room=words.amount(room_after))
    result = roster_flow.man_items(game, speech, Keys(END, ENTER, ENTER), store, section_of(game, store, spare_position(league)), man)
    assert asked in speech.said
    assert result.startswith(X.text("NXJ-S23", player=man.name, n=count - 1, m=53).rstrip())
    assert (man.status, man.team, man.salary, man.years, man.place, man.left) == ("free", 0, 0, 0, -1, league.season)
    assert league.dead[team - 1] == dead_before + dead
    assert real_roster.roster_count(league, team) == count - 1
    assert all(man.id not in ids for ids in league.chart[team - 1].values())
    assert man in S.pool(league)                                       # a free agent of this season: he may be signed again
    assert store.saves == 1


def test_escape_at_the_confirmation_releases_nobody():
    league = ready_league()
    game, store = franchise(league)
    man = lowest_releasable(league)
    count = real_roster.roster_count(league, league.team)
    result = roster_flow.man_items(game, Speech(), Keys(END, ENTER, ESC), store, section_of(game, store, spare_position(league)), man)
    assert result == X.text("NXJ-S24", player=man.name)
    assert man.status == "active" and man.team == league.team and real_roster.roster_count(league, league.team) == count
    assert store.saves == 0


# ----- the rules: hurt, the family minimums, the cap, when -----

def test_a_hurt_man_is_not_released(monkeypatch):
    league = ready_league()
    game, store = franchise(league)
    man = lowest_releasable(league)
    real = injuries.healthy
    monkeypatch.setattr(injuries, "healthy", lambda lg, pid, week: False if pid == man.id else real(lg, pid, week))
    result = SF.release_player(game, Speech(), Keys(ENTER), store, store.words, man)
    assert result == X.text("NXJ-S25", player=man.name)
    assert man.status == "active" and store.saves == 0


def test_the_last_kicker_is_not_released_the_family_minimum_holds():
    league = ready_league()
    game, store = franchise(league)
    kickers = [p for p in real_roster.members(league, league.team) if p.pos == "K"]
    assert len(kickers) == T.FR_FAMILY_MIN["K"] == 1
    result = SF.release_player(game, Speech(), Keys(ENTER), store, store.words, kickers[0])
    assert result == X.text("NXJ-S26", player=kickers[0].name, n=1, group="kicker")
    assert kickers[0].status == "active"


def test_the_quarterbacks_minimum_says_quarterbacks():
    league = ready_league()
    game, store = franchise(league)
    qbs = [p for p in real_roster.members(league, league.team) if p.pos == "QB"]
    for extra in qbs[2:]:
        S.release_alone(league, extra)                                 # down to the two a team must keep
    result = SF.release_player(game, Speech(), Keys(ENTER), store, store.words, qbs[1])
    assert result == X.text("NXJ-S26", player=qbs[1].name, n=2, group="quarterbacks")


def test_a_release_whose_dead_money_breaks_the_cap_is_refused():
    league = ready_league()
    game, store = franchise(league)
    man = lowest_releasable(league)
    man.salary, man.years = 2000, 8                                    # dead money twice his salary
    team = league.team
    league.dead[team - 1] += CT.cap_of(league) - CT.cap_used(league, team)      # the team is at the cap
    assert S.release_problem(league, man, league.gtp) == "over the cap"
    result = SF.release_player(game, Speech(), Keys(ENTER), store, store.words, man)
    assert result == X.text("NXJ-S16", room=store.words.amount(0))
    assert man.status == "active"


def test_no_release_during_a_game_in_the_offseason_or_before_the_week_is_prepared():
    from nfl4.extras.franchise.league import OFFSEASON
    league = ready_league()
    game, store = franchise(league, playing=True)
    man = lowest_releasable(league)
    assert SF.release_player(game, Speech(), Keys(ENTER), store, store.words, man) == X.text("NXJ-S27")
    game, store = franchise(league)
    league.prepared = [0, 0]
    assert SF.release_player(game, Speech(), Keys(ENTER), store, store.words, man) == X.text("NXJ-S29")
    league.prepared = [league.season, league.gtp]
    league.stage = OFFSEASON
    assert SF.release_player(game, Speech(), Keys(ENTER), store, store.words, man) == X.text("NXJ-S28")
    assert man.status == "active" and store.saves == 0


def test_a_release_is_open_in_the_play_offs_too():
    league = ready_league()
    league.gtp = league.regular_weeks + 1
    assert S.open_for_release(league, league.gtp) and not S.open_for_signing(league, league.gtp)


def test_a_starter_he_chose_who_is_released_names_the_new_starter_once():
    league = ready_league()
    game, store = franchise(league)
    from nfl4.extras import lineup as L
    key = spare_position(league)
    starter = chart_of(league, key)[0]
    league.depth = {"order": {key: [starter.id]}, "key": {}}
    result = SF.release_player(game, Speech(), Keys(ENTER), store, store.words, starter)
    new = league.players[league.chart[league.team - 1][key][0]]
    assert X.text("NXM-L75", old=starter.name, new=new.name, position=L.word(key)).strip() in result
    assert "dropped" not in league.depth                               # told here, so the roster does not tell it again


# ----- the free agents menu: release a player -----

def test_the_free_agents_menu_has_release_a_player_as_its_fourth_item():
    import inspect
    source = inspect.getsource(SF.free_agents_menu)
    assert source.index('"NXJ-P28"') < source.index('"NXJ-S20"')
    assert X.text("NXJ-S20") == "release a player"


def test_release_a_player_chooses_the_position_then_the_man():
    from nfl4.extras.franchise import positions as PS
    league = ready_league()
    game, store = franchise(league)
    speech = Speech()
    key = spare_position(league)
    man = chart_of(league, key)[-1]
    keys = [DOWN] * list(PS.ALL).index(key) + [ENTER] + [END, ENTER, ENTER]
    result = SF.release_flow(game, speech, Keys(*keys), store, store.words)
    assert result.startswith(X.text("NXJ-S23", player=man.name, n=real_roster.roster_count(league, league.team), m=53).rstrip())
    assert man.status == "free"
    assert any(X.text("NXJ-S31").strip() in t for t in speech.said)


# ----- the practice squad: released from the roster too, and "you did not release" -----

def squad_league():
    """A new franchise has its real practice squad: its first man."""
    from nfl4.extras.franchise import practice as P
    league = ready_league()
    return league, P.squad(league, league.team)[0]


def test_a_practice_squad_man_is_released_from_the_roster():
    league, man = squad_league()
    game, store = franchise(league)
    result = roster_flow.man_items(game, Speech(), Keys(END, ENTER, ENTER), store, section_of(game, store, "squad"), man)
    assert result == X.text("NXJ-P17", player=man.name)
    assert man.status == "free" and man.team == 0 and store.saves == 1


def test_escape_at_a_squad_release_says_you_did_not_release():
    league, man = squad_league()
    game, store = franchise(league)
    result = roster_flow.man_items(game, Speech(), Keys(END, ENTER, ESC), store, section_of(game, store, "squad"), man)
    assert result == X.text("NXJ-S24", player=man.name) and man.status == "practice"


# ----- the help, the key documents and the log -----

def test_the_key_list_and_the_readme_name_release_him():
    from pathlib import Path
    from nfl4.game import key_list
    row = next(row for row in key_list.ROWS if row.id == "roster")
    assert "release him" in row.what
    game = Path(__file__).resolve().parents[1]
    assert "release him" in (game / "README_keys.md").read_text(encoding="utf-8")


def test_a_release_and_a_refusal_are_logged(monkeypatch):
    from nfl4.data import debuglog
    events = []
    monkeypatch.setattr(debuglog, "event", lambda area, name, *rest, **fields: events.append((name, fields)))
    league = ready_league()
    game, store = franchise(league)
    man = lowest_releasable(league)
    SF.release_player(game, Speech(), Keys(ENTER), store, store.words, man)
    kicker = next(p for p in real_roster.members(league, league.team) if p.pos == "K")
    SF.release_player(game, Speech(), Keys(ENTER), store, store.words, kicker)
    names = [name for name, _ in events]
    assert "player_released" in names and "release_refused" in names
    released = dict(events)["player_released"]
    assert released["player"] == man.id and "dead_money" in released
    assert dict(events)["release_refused"]["reason"] == "a team would be short of a position"
