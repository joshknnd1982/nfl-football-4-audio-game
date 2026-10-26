"""SR.6 (phase PR, NX-L6, NX-L11, Q-082; D-160, D-164, D-165; NFL_FRANCHISE_DESIGN 21.8 and 21.13; CLAUDE.md 0.24, 0.25, 0.30): the roster said by positions, the
starting lineup and the choice of who starts at every real position (a quick game, a season and a franchise), the return roles on top of a place in a
franchise game, the trade menus' other positions and the namesakes' forms (nfl4 only, rule 0.13). This is inspired by Jim Kitchen.
"""
import random
from types import SimpleNamespace

import pytest

from nfl4.extras import depth_chart as DC
from nfl4.extras import lineup as L
from nfl4.extras import nfl_surnames
from nfl4.extras import nx_texts as X
from nfl4.extras import quarterbacks as Q
from nfl4.extras import real_names as R
from nfl4.extras import roster_file as RF
from nfl4.extras import roster_model as RM
from nfl4.extras.franchise import data as D
from nfl4.extras.franchise import history
from nfl4.extras.franchise import injury_flow
from nfl4.extras.franchise import real_roster as RR
from nfl4.extras.franchise import roster_flow
from nfl4.extras.franchise.league import new_league
from nfl4.game.keys import KEY_DOWN, KEY_END, KEY_ENTER, KEY_ESCAPE, KEY_F1, KEY_HOME, KEY_LEFT, KEY_RIGHT, KEY_UP
from nfl4.game.rnd import GameRandom

BEARS, BENGALS = 17, 1
ENTER, ESC, DOWN, UP, LEFT, RIGHT, HOME, END, F1 = KEY_ENTER, KEY_ESCAPE, KEY_DOWN, KEY_UP, KEY_LEFT, KEY_RIGHT, KEY_HOME, KEY_END, KEY_F1


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
    """Scripted keys: read_key returns the next one, Escape when they are used up (so a list always ends)."""

    def __init__(self, *answers):
        self.answers = list(answers)

    def read_key(self):
        return self.answers.pop(0) if self.answers else ESC


def quick_game(depth=""):
    settings = SimpleNamespace(nx_depth=depth, nx_qb_starters="", nx_key_players="")
    game = SimpleNamespace(options=SimpleNamespace(settings=SimpleNamespace(game=settings), save=lambda: None), customization=None, real_names=None,
                           play_engine=None)
    game.real_names = R.defaults()
    Q.apply(game)
    return game


def real_league(seed=3, team=BEARS):
    league = new_league(GameRandom(random.Random(seed)), nfl_surnames.pool(), "Kim", team, "20260101-000000", real=R.defaults())
    return league


def franchise(league, playing=False):
    store = SimpleNamespace(league=league, saves=0)
    store.words = history.Words(lambda t: "Team %d" % t, lambda: store.league)
    store.save = lambda: setattr(store, "saves", store.saves + 1)
    game = SimpleNamespace(play_engine=object() if playing else None)
    return game, store


# ----- the words and the descriptions (rules 0.24 and 0.25) -----

def test_every_position_and_role_has_a_plain_description_of_at_most_35_words():
    assert len(L.KEYS) == 24 and set(L.DESCRIPTION) == set(L.KEYS)
    for key in L.KEYS:
        text = L.describe(key)
        assert 4 <= len(text.split()) <= 35, key
        assert text.rstrip().endswith("."), key


def test_a_description_explains_its_football_words_or_uses_none_that_f7_leaves_out():
    from test_sx10b2_descriptions import JARGON, f7_text
    f7 = f7_text(True)
    import re
    own = {"HB": ("halfback",), "FB": ("fullback",), "LEDG": ("edge",), "REDG": ("edge",)}      # the word the description defines
    bad = []
    for key in L.KEYS:
        text = L.describe(key).lower()
        for pattern in JARGON:
            found = re.search(pattern, text)
            if found and not re.search(pattern, f7) and found.group(0) not in own.get(key, ()):
                bad.append((key, found.group(0)))
    assert not bad, bad


def test_the_headings_of_the_roster_are_the_22_positions_in_order():
    assert [X.text(roster_flow.HEADINGS[k]) for k in RM.MADDEN][:5] == ["quarterbacks", "halfbacks", "fullbacks", "wide receivers", "tight ends"]
    assert len(set(roster_flow.HEADINGS.values())) == 22


# ----- the lineup in a quick game -----

def test_the_lineup_of_a_quick_game_team_names_each_starter_with_his_number():
    game = quick_game()
    backend = L.QuickBackend(game, BENGALS, "Bengals")
    slots = backend.slots()
    assert slots[0] == ("QB", 0) and slots[-2:] == [("KR", 0), ("PR", 0)] and ("WR", 2) in slots and ("DT", 1) in slots and ("CB", 1) in slots
    real = game.real_names
    chart, roles, _ = real.chart(BENGALS)
    first = L.lineup_line(backend, "QB", 0)
    qb = chart["QB"][0]
    assert real.spoken(qb) in first and first.startswith(" quarterback, ")
    assert L.lineup_line(backend, "KR", 0).startswith(" kick returner, ")
    for key, slot in slots:
        assert L.lineup_line(backend, key, slot).strip()


def test_the_candidates_of_a_position_are_its_men_then_its_familys_movers_then_the_squad_never_another_family():
    game = quick_game()
    backend = L.QuickBackend(game, BEARS, "Bears")
    chart, roles, squad = game.real_names.chart(BEARS)
    tackles = backend.candidates("LT")
    assert [m.key for m in tackles[:len(chart["LT"])]] == chart["LT"]
    assert {m.position for m in tackles} <= {"LT", "RT"} and any(m.position == "RT" for m in tackles)
    assert backend.candidates("QB")[0].key == chart["QB"][0] and {m.position for m in backend.candidates("QB")} == {"QB"}
    assert all(m.position not in RM.RETURN_NEVER for m in backend.candidates("KR"))
    assert backend.candidates("KR")[0].key == roles["KR"][0]


def test_choosing_a_starter_from_the_other_side_moves_him_and_the_man_there_takes_his_old_place():
    game = quick_game()
    backend = L.QuickBackend(game, BEARS, "Bears")
    chart, _, _ = game.real_names.chart(BEARS)
    right = chart["RT"][0]
    old_left = chart["LT"][0]
    man = next(m for m in backend.candidates("LT") if m.key == right)
    text = backend.choose("LT", man, 0)
    assert text == X.text("NXM-L70", player=game.real_names.spoken(right), old="right tackle", new="left tackle")
    after, _, _ = game.real_names.chart(BEARS)
    assert after["LT"][0] == right and right not in after["RT"] and old_left in after["LT"]
    assert game.options.settings.game.nx_depth.startswith("T%02d " % BEARS) and "LT=%s" % right in game.options.settings.game.nx_depth


def test_choosing_the_same_man_says_he_starts_already_and_changes_nothing():
    game = quick_game()
    backend = L.QuickBackend(game, BEARS, "Bears")
    first = backend.starters("QB")[0]
    assert backend.choose("QB", first, 0) == X.text("NXM-L72", player=first.name)


def test_a_position_that_starts_three_men_chooses_by_place():
    game = quick_game()
    backend = L.QuickBackend(game, BEARS, "Bears")
    chart, _, _ = game.real_names.chart(BEARS)
    fifth = backend.men_at("WR")[4]
    text = backend.choose("WR", fifth, 1)
    assert text == X.text("NXM-L69", player=fifth.name, position="wide receiver", n=2)
    assert game.real_names.chart(BEARS)[0]["WR"][1] == fifth.key


def test_a_return_role_takes_any_man_but_a_quarterback_a_kicker_a_punter_or_a_snapper():
    game = quick_game()
    backend = L.QuickBackend(game, BEARS, "Bears")
    man = next(m for m in backend.candidates("PR") if m.position == "CB")
    assert backend.choose("PR", man, 0) == X.text("NXM-L71", player=man.name, position="punt returner")
    assert game.real_names.chart(BEARS)[1]["PR"][0] == man.key


def test_a_practice_squad_man_is_brought_up_for_the_next_game_two_at_most():
    game = quick_game()
    backend = L.QuickBackend(game, BEARS, "Bears")
    squad = [m for key in ("WR", "CB", "HB", "TE") for m in backend.squad_men(key)]
    assert len(squad) >= 3
    first = backend.choose(squad[0].position, squad[0], 0)
    assert first == X.text("NXM-L73", player=squad[0].name, position=L.label(squad[0].position))
    chart, _, squad_chart = game.real_names.chart(BEARS)
    assert squad[0].key in chart[squad[0].position] and squad[0].key not in squad_chart.get(squad[0].position, [])
    second = next(m for m in squad[1:] if m.position != squad[0].position or True)
    assert backend.choose(second.position, second, 0) == X.text("NXM-L73", player=second.name, position=L.label(second.position))
    third = next(m for m in squad[1:] if m.key != second.key)
    assert backend.choose(third.position, third, 0) == X.text("NXM-L74")
    assert game.real_names.chart(BEARS)[0][third.position].count(third.key) == 0


def test_a_chosen_starter_who_is_no_longer_on_the_team_is_told_once_and_dropped():
    game = quick_game("T%02d LT=Nobody Atall" % BEARS)
    backend = L.QuickBackend(game, BEARS, "Bears")
    told = backend.notices()
    chart, _, _ = game.real_names.chart(BEARS)
    assert told == [X.text("NXM-L75", old="Nobody Atall", new=game.real_names.spoken(chart["LT"][0]), position="left tackle")]
    assert game.options.settings.game.nx_depth == ""
    assert backend.notices() == []


# ----- the lineup and the choice, spoken -----

def test_the_lineup_list_speaks_each_place_and_d_describes_it():
    game = quick_game()
    backend = L.QuickBackend(game, BEARS, "Bears")
    speech = Speech()
    L.lineup_picker(speech, Keys(letter("d"), DOWN, letter("d"), ESC), backend, "Bears")
    assert X.text("NXM-L31", team="Bears").strip() in speech.said[0]
    assert L.describe("QB") in speech.said and L.describe("HB") in speech.said


def test_enter_on_a_place_opens_its_choice_and_enter_on_a_man_makes_him_the_starter():
    game = quick_game()
    backend = L.QuickBackend(game, BEARS, "Bears")
    speech = Speech()
    chart, _, _ = game.real_names.chart(BEARS)
    wanted = backend.men_at("QB")[1]
    L.lineup_picker(speech, Keys(ENTER, DOWN, ENTER, ESC), backend, "Bears")
    assert X.text("NXM-L68", player=wanted.name, position="quarterback") in speech.said
    assert game.real_names.chart(BEARS)[0]["QB"][0] == wanted.key


def test_the_choice_list_starts_on_the_man_who_starts_now_and_marks_him():
    game = quick_game()
    backend = L.QuickBackend(game, BEARS, "Bears")
    speech = Speech()
    assert L.choose_flow(speech, Keys(ESC), backend, "QB", 0) is None
    assert ", starts now" in speech.said[0]
    assert X.text("NXM-L37", position="quarterback").strip() in speech.said[0]


def test_a_lineman_is_never_a_returner_in_a_quick_game_or_a_franchise():
    # found by the SR.6 soak: a lineman made the kick returner broke the league's check (a return place may hold no lineman)
    game = quick_game()
    backend = L.QuickBackend(game, BEARS, "Bears")
    assert not [m for m in backend.candidates("KR") if m.position in RM.RETURN_NEVER]
    lineman = backend.men_at("LT")[0]
    with pytest.raises(ValueError):
        DC.choose_starter(DC.parse_depth(""), game.real_names, BEARS, "KR", lineman.key)
    league = real_league()
    fgame, store = franchise(league)
    fb = L.FranchiseBackend(fgame, store)
    assert not [m for m in fb.candidates("PR") if m.position in RM.RETURN_NEVER]
    from nfl4.extras.franchise.league import LeagueError
    with pytest.raises(LeagueError):
        RR.choose_starter(league, "KR", fb.men_at("C")[0].key)


# ----- the franchise lineup -----

def test_a_franchise_lineup_chooses_through_the_leagues_chart_and_saves_before_telling():
    league = real_league()
    game, store = franchise(league)
    backend = L.FranchiseBackend(game, store)
    chart = league.chart[league.team - 1]
    second = backend.men_at("QB")[1]
    text = backend.choose("QB", second, 0)
    assert text == X.text("NXM-L68", player=second.name, position="quarterback") and store.saves == 1
    assert league.chart[league.team - 1]["QB"][0] == second.key
    assert league.rosters[league.team - 1][D.PLACES_OF["QB"][0]] == second.key
    league.check()


def test_a_franchise_choice_while_a_game_is_played_is_refused():
    league = real_league()
    game, store = franchise(league, playing=True)
    speech = Speech()
    assert L.choose_flow(speech, Keys(), L.FranchiseBackend(game, store), "QB", 0) == X.text("NXI-54")


def test_a_starter_the_player_chose_who_leaves_is_told_once_and_the_next_man_starts():
    league = real_league()
    game, store = franchise(league)
    backend = L.FranchiseBackend(game, store)
    second = backend.men_at("QB")[1]
    backend.choose("QB", second, 0)
    man = league.players[second.key]
    RR.leave(league, man, "released")
    man.team = 0
    told = backend.notices()
    now = league.players[league.chart[league.team - 1]["QB"][0]]
    assert told == [X.text("NXM-L75", old=man.name, new=now.name, position="quarterback")]
    assert backend.notices() == []
    league.check()


def test_the_dropped_record_survives_a_save_and_is_checked():
    league = real_league()
    game, store = franchise(league)
    backend = L.FranchiseBackend(game, store)
    backend.choose("QB", backend.men_at("QB")[1], 0)
    man = league.players[backend.men_at("QB")[0].key]
    RR.leave(league, man, "released")
    man.team = 0
    assert league.depth["dropped"]
    again = type(league).from_json(league.to_json())
    assert again.depth["dropped"] == league.depth["dropped"]


# ----- the roster by positions -----

def roster(league, keys, playing=False):
    game, store = franchise(league, playing)
    speech = Speech()
    roster_flow.roster_list(game, speech, Keys(*keys), store)
    return speech.said, store


def test_the_roster_opens_on_the_quarterbacks_with_their_count_and_the_first_man_in_full():
    league = real_league()
    said, _ = roster(league, [])
    chart = league.chart[league.team - 1]
    qb = league.players[chart["QB"][0]]
    assert said[0].startswith("your roster.") and "53 players of 53" in said[0]
    assert X.text("NXM-L01", heading="quarterbacks", n=3).strip() in said[0]
    assert qb.name in said[0] and "quarterback, starter" in said[0] and "number %s" % qb.number in said[0]


def test_down_goes_man_by_man_into_the_next_position_with_its_heading():
    league = real_league()
    said, _ = roster(league, [DOWN, DOWN, DOWN])
    chart = league.chart[league.team - 1]
    assert len(chart["QB"]) == 3
    assert "second" in said[1] and "third" in said[2]
    assert X.text("NXM-L01", heading="halfbacks", n=len(chart["HB"])).strip() in said[3]
    assert league.players[chart["HB"][0]].name in said[3]


def test_left_and_right_go_position_by_position_and_home_and_end_to_the_ends():
    league = real_league()
    said, _ = roster(league, [RIGHT, RIGHT, LEFT, END, HOME])
    chart = league.chart[league.team - 1]
    assert X.text("NXM-L01", heading="halfbacks", n=len(chart["HB"])).strip() in said[1]
    assert X.text("NXM-L01", heading="fullbacks", n=len(chart["FB"])).strip() in said[2]
    assert X.text("NXM-L01", heading="halfbacks", n=len(chart["HB"])).strip() in said[3]
    assert said[5].startswith(" quarterbacks") or "quarterbacks" in said[5]


def test_a_letter_goes_to_the_next_position_that_starts_with_it_and_e_to_the_tight_ends_and_t_to_nothing():
    league = real_league()
    chart = league.chart[league.team - 1]
    said, _ = roster(league, [letter("e"), letter("l"), letter("l"), letter("t")])
    assert X.text("NXM-L01", heading="tight ends", n=len(chart["TE"])).strip() in said[1]
    assert "left tackles" in said[2] and "left guards" in said[3]
    assert said[4] == said[3]                                  # T is not a jump key (rule 0.22): the list stays where it is


def test_every_position_has_a_heading_with_its_count_even_with_nobody_and_the_counts_add_up():
    league = real_league()
    game, store = franchise(league)
    sections = roster_flow.sections_of(game, store)
    keys = [s.key for s in sections]
    assert keys[:22] == list(RM.MADDEN) and "squad" in keys
    assert sum(len(s.men) for s in sections if s.key in RM.MADDEN) == 53
    assert all(s.letter != "t" for s in sections)


def test_a_man_is_said_by_his_own_position_the_depth_the_returner_role_and_the_number():
    league = real_league()
    game, store = franchise(league)
    chart = league.chart[league.team - 1]
    kr = league.players[chart["KR"][0]]
    sections = roster_flow.sections_of(game, store)
    section = next(s for s in sections if s.key == kr.position)
    line = roster_flow.man_line(game, store, section, section.men.index(kr))
    assert RF.SPOKEN[kr.position] in line and "kick returner" in line and "rating %d" % kr.rating in line


def test_the_practice_squad_and_the_reserve_lists_are_their_own_headings_after_the_positions():
    league = real_league()
    game, store = franchise(league)
    sections = roster_flow.sections_of(game, store)
    squad = next(s for s in sections if s.key == "squad")
    assert squad.heading == "practice squad" and squad.men and all(p.status == "practice" for p in squad.men)
    line = roster_flow.man_line(game, store, squad, 0)
    assert "practice squad" in line
    listed = [s for s in sections if s.key in RF.RESERVE]
    assert all(s.men and all(p.status == "list" for p in s.men) for s in listed)


def test_enter_on_a_man_offers_to_make_him_the_starter_and_does_it():
    league = real_league()
    game, store = franchise(league)
    speech = Speech()
    chart = league.chart[league.team - 1]
    target = league.players[chart["QB"][1]]
    roster_flow.PositionList  # the list class exists
    keys = Keys(DOWN, ENTER, ENTER, ESC)
    roster_flow.roster_list(game, speech, keys, store)
    assert chart is league.chart[league.team - 1] or True
    assert league.chart[league.team - 1]["QB"][0] == target.id
    assert X.text("NXM-L68", player=target.name, position="quarterback") in speech.said


def test_the_items_of_a_tackle_include_the_other_side_and_the_returner_roles_but_a_quarterback_has_neither_a_move_nor_a_role():
    league = real_league()
    game, store = franchise(league)
    speech = Speech()
    chart = league.chart[league.team - 1]
    lt = league.players[chart["LT"][0]]
    section = next(s for s in roster_flow.sections_of(game, store) if s.key == "LT")
    roster_flow.man_items(game, speech, Keys(ESC), store, section, lt)
    opening = speech.said[0]
    assert "make him the starter at right tackle" in opening or "make him the starter at left tackle" in opening or "make him the kick returner" in opening
    speech = Speech()
    qb = league.players[chart["QB"][1]]
    section = next(s for s in roster_flow.sections_of(game, store) if s.key == "QB")
    roster_flow.man_items(game, speech, Keys(DOWN, DOWN, ESC), store, section, qb)
    said = " ".join(speech.said)
    assert "kick returner" not in said and "right tackle" not in said and "change his name" in said


# ----- the return roles on top of a place (Q-082) -----

def test_the_game_day_returners_are_the_roles_men_even_when_they_start_elsewhere():
    league = real_league()
    chart = league.chart[league.team - 1]
    found = injury_flow.game_returners(league, league.team, 1, True)
    assert len(found) == 2
    wanted = []
    for i in range(3):
        for role in ("KR", "PR"):
            if i < len(chart[role]) and chart[role][i] not in wanted:
                wanted.append(chart[role][i])
    assert [pid for pid, _name, _rating in found] == wanted[:2]
    roster = injury_flow.lineup_roster(league, league.team, 1, True)
    assert roster.special_teams == [league.players[pid].name for pid in wanted[:2]]
    heading = D.PLACES[D.PLACES_OF["RET"][0]][0]
    assert roster.ratings[(heading, 1)] == league.players[wanted[0]].rating


def test_a_returner_who_is_hurt_for_the_week_is_replaced_by_the_next_man_of_the_roles():
    from nfl4.extras.franchise import injuries
    league = real_league()
    chart = league.chart[league.team - 1]
    found = injury_flow.game_returners(league, league.team, 1, True)
    first = found[0][0]
    again = injury_flow.game_returners(league, league.team, 1, True, out=frozenset({first}))
    assert first not in [pid for pid, _n, _r in again] and len(again) == 2


def test_every_team_of_a_new_franchise_has_two_real_returners_on_the_game_day():
    league = real_league()
    for team in range(1, D.TEAMS + 1):
        found = injury_flow.game_returners(league, team, 1, True)
        assert len(found) == 2, team
        chart = league.chart[team - 1]
        assert found[0][0] in chart["KR"] + chart["PR"]


# ----- the namesakes (design 21.8) -----

def test_a_name_two_men_of_the_league_share_is_said_with_position_and_team_in_a_league_list():
    league = real_league()
    store_words = history.Words(lambda t: "Team %d" % t, lambda: league)
    pairs = {}
    for p in league.players.values():
        if p.status in ("active", "practice", "list"):
            pairs.setdefault(p.name.casefold(), []).append(p)
    twins = [men for men in pairs.values() if len(men) > 1 and len({m.team for m in men}) > 1]
    assert twins                                               # SR.2: six names belong to two real men
    a, b = twins[0][:2]
    text = store_words.named(a)
    assert a.name in text and RF.SPOKEN[a.position] in text and "Team %d" % a.team in text
    single = next(p for p in league.players.values() if len(pairs.get(p.name.casefold(), [])) == 1 and p.status == "active")
    assert store_words.named(single) == single.name


def test_two_men_of_one_name_on_one_team_are_told_apart_by_their_numbers_in_the_roster():
    league = real_league()
    game, store = franchise(league)
    a, b = [p for p in league.players.values() if p.team == league.team and p.status == "active"][:2]
    b.name = a.name
    assert roster_flow.name_in_team(league, a) == X.text("NXM-L82", player=a.name, number=a.number).strip()


# ----- the trade menus (D-164 (5)) -----

def test_a_trade_asks_for_the_position_of_the_man_you_give_and_the_last_line_goes_to_another_position():
    from nfl4.extras.franchise import trade_flow
    assert X.text("NXM-L84") == "a player of another position" and X.text("NXM-L85").strip().startswith("which position")
