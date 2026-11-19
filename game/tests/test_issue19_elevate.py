"""GitHub issue 19 (D-247, D-248): "No way to elevate a practice squad player" (nfl4 only, rule 0.13; AGENTS.md 0.34). This is inspired by Jim Kitchen.

The tester (Dennisl123, 2026-11-18, on 1.0.5): "If a player is hurt you should be able to elevate a player. This is not possible. see log." His problem
report: the Chiefs' punter Matt Araiza out for 3 games, no other punter, so the staff signed a made-up stand-in ("Logan Broomfield fills in at
punter"); injured reserve was refused (too few punters); he added the punter Johnny Hekker to his practice squad and found no way to play him.

What is tested: the who-starts choices (the to-do item and F9's injury report) offer the squad men of the place's family after the roster's men, and
when nobody of the team can play the place the staff's stand-in comes first and the squad men follow; the chosen squad man plays the place this week at
his own rating but never above the hurt man's, as a stand-in (never hurt); the staff setting and other teams ignore the choice; the NFL's limits (3 a
regular season, any number in the play-offs, 2 a game with the staff's own, one place a man); the game counts the elevation when it is played and sends
him back to the squad; the week's settle drops a leftover choice; the injury report does not name the made-up stand-in while the squad man plays; the
practice squad's new item elevates, says why not, and sends a man back; the league file keeps the choice. D-248: a code no key sends (vk 252, which
the tester's game got 13 times while he held Alt with JAWS running) is dropped, so the menu does not repeat its item.
"""
import json
import random
from types import SimpleNamespace

import pytest
from drrig import SURNAMES
from test_fr_practice import formed
from test_lineup_sr6 import DOWN, ENTER, ESC, Keys, Speech, franchise

from nfl4.extras import nx_texts as X
from nfl4.extras.franchise import data as D
from nfl4.extras.franchise import history
from nfl4.extras.franchise import injuries as I
from nfl4.extras.franchise import injury_flow as F
from nfl4.extras.franchise import practice as P
from nfl4.extras.franchise import practice_flow as PF
from nfl4.extras.franchise import real_roster as RR
from nfl4.extras.franchise import signings as S
from nfl4.extras.franchise.league import LeagueRecord
from nfl4.game.keys import NOT_KEYS, KeyInput
from nfl4.game.rnd import GameRandom

TEAM = 5                                              # the player's team of test_fr_practice.formed
WEEK = 3
WORDS = history.Words(lambda team: "Team%d" % team)


def punter_case():
    """The tester's case: the player's only punter out for 3 games, the staff's made-up stand-in, a free-agent punter added to the squad after it."""
    league = formed()
    assert league.team == TEAM
    for man in [p for p in P.squad(league, TEAM) if p.pos == "P"]:
        P.release_from_squad(league, man)                 # no punter on the squad when the stand-in is signed
    punters = [p for p in RR.members(league, TEAM) if p.pos == "P"]
    for man in punters:
        I.injure(league, man.id, "IJB", 3, 0, WEEK - 1)   # hurt in week 2: out for weeks 3 to 5
    I.settle(league, WEEK, GameRandom(random.Random(5)), SURNAMES)
    league.gtp = WEEK
    row = I.stand_in(league, TEAM, "P")
    assert row is not None and row[2] not in P.names(league, TEAM)           # a made-up man, as "Logan Broomfield"
    S.ensure_pool(league, SURNAMES)
    agent = next(p for p in S.pool(league) if p.pos == "P")
    P.sign_to_squad(league, agent)
    starter = next(p for p in punters if p.place >= 0)
    league.prepared = [league.season, WEEK]                # the week's preparation is done: F9's menus are open
    return league, starter, agent, row


def squad_men(league, position):
    return [p for p in P.squad(league, TEAM) if p.pos == position]


def checked(league):
    """league.check() with the week the fixture's season can be checked at (formed() has no schedule; the rows do not depend on the week)."""
    week, league.gtp = league.gtp, 1
    try:
        league.check()
        return LeagueRecord.from_json(league.to_json())
    finally:
        league.gtp = week


def hurt(league, man, week=WEEK, games=3):
    I.injure(league, man.id, "IJB", games, 0, week - 1)


# ----- the choices and the lineup -----

def test_the_testers_case_offers_the_squad_punter_after_the_staffs_stand_in():
    league, starter, agent, row = punter_case()
    choices = I.cover_choices(league, starter.id, WEEK)
    assert isinstance(choices[0], I.StandInChoice) and choices[0].name == row[2] and not choices[0].squad
    assert [c.id for c in choices[1:]] == [agent.id]
    assert starter.id in I.to_choose(league, WEEK)                          # the to-do list asks about his place now
    situation, answers = F.lineup_view(WORDS, league, F.lineup_item(league, WEEK, starter.id))
    assert answers[0] == X.text("NXI-A05", player=row[2], position=WORDS.position("P"))
    assert answers[1] == X.text("NXI-A07", player=agent.name, position=WORDS.position_for(agent), r=agent.rating, a=agent.age, n=P.ELEVATIONS)


def test_the_chosen_squad_man_plays_the_place_as_a_stand_in_and_never_above_the_hurt_man():
    league, starter, agent, row = punter_case()
    I.choose(league, starter.id, agent.id)
    table = I.lineup(league, TEAM, WEEK, staff=False)
    assert table[starter.place] == ((I.STAND_IN, "P"), agent.name, min(agent.rating, starter.rating))
    assert I.lineup(league, TEAM, WEEK, staff=True)[starter.place][1] == row[2]          # the staff setting keeps the staff's rule
    found = []
    I.lineup(league, TEAM, WEEK, staff=False, elevated=found)
    assert found == [agent]
    assert F.starter_name(league, starter.id, WEEK) == agent.name
    assert any(X.text("NXI-62", player=starter.name, get=agent.name) == line for line, _key in F.list_lines(WORDS, league, WEEK, False))
    assert F.starts_text(league, starter.id, agent) == X.text("NXI-65", get=agent.name, give=starter.name)
    again = checked(league)
    assert [starter.id, agent.id] in again.injuries["chosen"]


def test_the_report_does_not_name_the_made_up_stand_in_while_the_squad_man_plays():
    league, starter, agent, row = punter_case()
    told = X.text("NXI-21", player=row[2], position=WORDS.position("P"))
    assert told in F.report_lines(league, WEEK, [], WORDS, None, GameRandom(random.Random(1)))
    I.choose(league, starter.id, agent.id)
    assert told not in F.report_lines(league, WEEK, [], WORDS, None, GameRandom(random.Random(1)))


def test_a_roster_mans_choices_end_with_the_squad_men_of_the_family():
    league = formed()
    league.gtp = WEEK
    man = league.player_at(TEAM, D.PLACES_OF["WR"][0])
    hurt(league, man)
    choices = I.cover_choices(league, man.id, WEEK)
    roster = [c for c in choices if c.status == "active"]
    squad = [c for c in choices if c.status == P.STATUS]
    assert choices[:len(roster)] == roster and squad and choices[len(roster):] == squad
    assert all(c.pos in P.PLACE_FAMILIES.get("WR", ("WR",)) for c in squad)
    assert [c.id for c in squad] == [p.id for p in P.eligible(league, TEAM, "WR", WEEK)]


def test_the_limits_three_a_season_any_number_in_the_play_offs():
    league, starter, agent, _row = punter_case()
    league.practice["elevations"][str(agent.id)] = P.ELEVATIONS
    assert I.cover_choices(league, starter.id, WEEK) == []                 # only the staff's stand-in is left: nothing to ask
    assert P.elevate_problem(league, agent, WEEK) == "no elevations left"
    playoff = league.regular_weeks + 1
    assert P.elevate_problem(league, agent, playoff) is None
    assert agent in P.elevation_choices(league, starter.id, playoff, staff_name=I.stand_in(league, TEAM, "P")[2])


def test_two_a_game_and_one_place_a_man():
    league, starter, agent, _row = punter_case()
    receivers = squad_men(league, "WR")
    assert len(receivers) >= 2
    first, second = (league.player_at(TEAM, D.PLACES_OF["WR"][k]) for k in (0, 1))
    hurt(league, first)
    hurt(league, second)
    I.choose(league, first.id, receivers[0].id)
    assert receivers[0] not in P.elevation_choices(league, second.id, WEEK)            # one place a man
    assert receivers[1] in P.elevation_choices(league, second.id, WEEK)
    I.choose(league, second.id, receivers[1].id)
    assert P.elevation_choices(league, starter.id, WEEK, staff_name=I.stand_in(league, TEAM, "P")[2]) == []     # the game's two are taken
    assert receivers[0] in P.elevation_choices(league, first.id, WEEK)                 # his own place keeps its choice
    table = I.lineup(league, TEAM, WEEK, staff=False)
    assert {table[first.place][1], table[second.place][1]} == {receivers[0].name, receivers[1].name}


def test_the_staffs_own_elevation_counts_in_the_games_two():
    league = formed()
    league.gtp = WEEK
    quarterbacks = squad_men(league, "QB")
    if not quarterbacks:
        S.ensure_pool(league, SURNAMES)
        P._join(league, TEAM, next(p for p in S.pool(league) if p.pos == "QB"))
        quarterbacks = squad_men(league, "QB")
    for man in RR.members(league, TEAM):
        if man.pos == "QB":
            hurt(league, man, games=5)
    I.settle(league, WEEK, GameRandom(random.Random(5)), SURNAMES)
    assert I.stand_in(league, TEAM, "QB")[2] in P.names(league, TEAM)                # the staff brought up its squad quarterback (D-136)
    assert len(P.staff_elevated(league, TEAM, WEEK)) == 1
    receivers = squad_men(league, "WR")
    first, second = (league.player_at(TEAM, D.PLACES_OF["WR"][k]) for k in (0, 1))
    hurt(league, first)
    hurt(league, second)
    I.choose(league, first.id, receivers[0].id)
    assert P.elevation_choices(league, second.id, WEEK) == []                        # the staff's one and the player's one


# ----- after the game and the week -----

def test_the_game_counts_the_elevation_and_sends_him_back_to_the_squad():
    league, starter, agent, row = punter_case()
    I.choose(league, starter.id, agent.id)
    assert P.after_game(league, TEAM, WEEK, staff=False) == [(agent.id, 1)]
    assert P.elevations(league, agent) == 1 and agent.status == P.STATUS
    assert P.picks(league) == {} and I.lineup(league, TEAM, WEEK, staff=False)[starter.place][1] == row[2]
    checked(league)


def test_the_play_offs_count_none_and_the_staff_setting_brings_nobody_up():
    league, starter, agent, _row = punter_case()
    I.row_of(league, starter.id)[3] = league.regular_weeks + 4             # still hurt in the play-offs
    I.choose(league, starter.id, agent.id)
    assert P.after_game(league, TEAM, league.regular_weeks + 1, staff=False) == [(agent.id, 0)]
    assert P.elevations(league, agent) == 0
    I.choose(league, starter.id, agent.id)
    assert P.after_game(league, TEAM, WEEK, staff=True) == [] and P.elevations(league, agent) == 0 and P.picks(league) == {}


def test_the_games_commit_counts_it():
    league, starter, agent, _row = punter_case()
    I.choose(league, starter.id, agent.id)
    other = next(t for t in range(1, D.TEAMS + 1) if t != TEAM)
    game = F.GameInjuries(league, TEAM, other, WEEK, False, GameRandom(random.Random(2)), SURNAMES, WORDS)
    game.state = SimpleNamespace(extras=SimpleNamespace(injuries=None))
    game.commit()
    assert P.elevations(league, agent) == 1 and P.picks(league) == {}


def test_the_weeks_settle_drops_a_squad_choice_and_keeps_a_roster_choice():
    league, starter, agent, _row = punter_case()
    man = league.player_at(TEAM, D.PLACES_OF["DL"][0])
    hurt(league, man, games=5)
    roster_pick = next(c for c in I.cover_choices(league, man.id, WEEK)[1:] if c.status == "active")
    I.choose(league, man.id, roster_pick.id)
    I.choose(league, starter.id, agent.id)
    I.settle(league, WEEK + 1, GameRandom(random.Random(5)), SURNAMES)
    assert I.chosen_map(league) == {man.id: roster_pick.id}


# ----- the practice squad's item -----

def walk_to(league, player):
    return [DOWN] * P.squad(league, TEAM).index(player)


def test_the_item_elevates_the_squad_man_and_enter_on_him_again_sends_him_back():
    league, starter, agent, row = punter_case()
    game, store = franchise(league)
    said = PF.elevate_flow(game, Speech(), Keys(*walk_to(league, agent), ENTER, ENTER), store, store.words)
    assert said == X.text("NXI-65", get=agent.name, give=starter.name)
    assert P.picks(league) == {starter.id: agent.id} and store.saves == 1
    assert X.text("NXJ-P62", player=starter.name) in PF.squad_line(store.words, league, agent)
    said = PF.elevate_flow(game, Speech(), Keys(*walk_to(league, agent), ENTER, ENTER), store, store.words)
    assert said == X.text("NXJ-P71", player=agent.name, get=row[2], give=starter.name)
    assert P.picks(league) == {} and store.saves == 2


def test_the_item_says_why_not_and_changes_nothing():
    league, starter, agent, _row = punter_case()
    game, store = franchise(league)
    keys = Keys(*walk_to(league, agent), ENTER, ESC)
    assert PF.elevate_flow(game, Speech(), keys, store, store.words) == X.text("NXI-R40", player=agent.name)
    league.practice["elevations"][str(agent.id)] = P.ELEVATIONS
    assert PF.elevate_flow(game, Speech(), Keys(*walk_to(league, agent), ENTER), store, store.words) == \
        X.text("NXJ-P63", player=agent.name, n=P.ELEVATIONS)
    quarterback = next(p for p in P.squad(league, TEAM) if p.pos == "QB")
    assert PF.elevate_flow(game, Speech(), Keys(*walk_to(league, quarterback), ENTER), store, store.words) == \
        X.text("NXJ-P65", player=quarterback.name)
    assert P.picks(league) == {} and store.saves == 0
    playing, store2 = franchise(league, playing=True)
    assert PF.elevate_flow(playing, Speech(), Keys(), store2, store2.words) == X.text("NXJ-P10")


def test_the_menu_has_the_item_second_and_the_help_and_rules_say_it():
    import inspect
    source = inspect.getsource(PF.practice_menu)
    assert source.index("NXJ-P20") < source.index("NXJ-P60") < source.index("NXJ-P21")
    assert "elevate a player for this game" in X.text("NXH-74") and "protect squad players" in X.text("NXH-74")
    assert "in place of a hurt player" in X.text("NXJ-P35") and "elevated" in X.text("NXH-72")
    from nfl4.extras.franchise import menus
    lines = menus.HELP_LINES["117"]
    assert lines.index("NXH-90") == lines.index("NXH-42") + 1
    assert "elevate" in X.text("NXI-R30", player="Matt Araiza")


def test_the_texts_module_is_exactly_the_master_table():
    """B-T160: 1.0.6's texts NXM-D15 to NXM-D17 were written into nx_texts.py by hand and never into spec/strings_nx.tsv, so this session's
    generation dropped them; the generated module must hold every row of the table, as the table has it, and nothing else."""
    import pathlib
    table = pathlib.Path(__file__).resolve().parents[2] / "spec" / "strings_nx.tsv"
    rows = [line.split("\t") for line in table.read_bytes().decode("utf-8").split("\n")[1:] if line]
    assert [row[0] for row in rows if X.TEXTS.get(row[0]) != row[4] or X.SPEAKERS.get(row[0]) != row[3] or X.KINDS.get(row[0]) != row[2]] == []
    assert set(X.TEXTS) == {row[0] for row in rows} and len(rows) == len(X.TEXTS)
    assert all(len(row[4]) <= 200 for row in rows)


# ----- D-248: codes no key sends -----

def test_a_code_no_key_sends_is_dropped_and_a_real_key_is_kept():
    keys = KeyInput()
    for code in (252, 0xE8, 0x07, 0xFF):
        assert code in NOT_KEYS
        keys.post(code)
    assert not keys.key_waiting()
    keys.post(13)
    assert keys.key_waiting()
    real = set(range(0x08, 0x0A)) | {0x0D, 0x10, 0x11, 0x12, 0x1B, 0x20} | set(range(0x21, 0x2F)) | set(range(0x30, 0x3A)) | \
        set(range(0x41, 0x5B)) | set(range(0x60, 0x88)) | {0x90, 0x91} | set(range(0xBA, 0xC1)) | set(range(0xDB, 0xE0))
    assert not (real & NOT_KEYS)
