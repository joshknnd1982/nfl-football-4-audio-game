"""The playbooks' menus and the computer's choice (nfl4 only, rule 0.13; NFL_EXTRAS_DESIGN 10.4, NX5 N5.5 and N5.6; PX SX.7).
This is inspired by Jim Kitchen.

The two-level menu of a style (groups, then plays, Back, Backspace and Left), the original's menu for Classic, the computer's
weighted draws on a strict scripted source, the situation's percents and what is never touched (kicks, the try, Classic). Every
expected text and number is worked out from the data and the tuning next to it (B-X38).
"""
import pytest

from nfl4.extras import nx_texts as X
from nfl4.extras import playbook_data as D
from nfl4.extras import playbooks as PB
from nfl4.extras import tuning as T
from nfl4.extras.nfl_rules import NflRules
from nfl4.extras.qb_runs import to_goal
from nfl4.game import menus
from nfl4.game import phrases as P
from nflrig import nfl_engine_rig
from pagrig import Draws, run_steps
from randsources import ScriptedRandom

ENTER, ESCAPE, UP, DOWN, BACKSPACE, LEFT = 13, 27, 38, 40, 8, 37
SELECT = " Kim" + P.SELECT_OFFENSE
SELECT_D = " Kim" + P.SELECT_DEFENSE
MENU_UNTIL = ("offense_chosen", "defense_chosen", "concede", "save_game")
START = dict(wisoff=1, defense=2, half=2, yard_line=30, down=1, to_go=10, quarter=1)
TABLE = PB.DEFAULT_TABLE


def rig_for(tmp_path, answers=(), offense="west", defense="classic", qb_on=False, timeouts_on=False, computer=False, **state):
    fields = dict(START)
    fields.update(state)
    rules = NflRules(timeouts_on=timeouts_on, qb_on=qb_on, offense_book=offense, defense_book=defense, playbooks_on=computer)
    return nfl_engine_rig(tmp_path, answers=list(answers), rules=rules, **fields)


def texts(rig, start=0):
    return [t for t, _, _ in rig.said[start:]]


def items_of(rig, defense=False):
    s = rig.engine.s
    return [i.text for i in (rig.rules.defense_menu(s) if defense else rig.rules.offense_menu(s, False))]


def the_menu(rig, defense=False):
    return run_steps(rig, rig.engine.defense_menu if defense else rig.engine.offense_menu, Draws(), until=MENU_UNTIL)


# ----- the player's books -----

def test_the_players_book_is_classic_the_teams_style_or_a_style_and_the_computers_is_its_teams(tmp_path):
    rig = rig_for(tmp_path, offense="classic", defense="classic")
    assert rig.engine.s.extras.offense_book == ["classic", "classic"] == rig.engine.s.extras.defense_book
    rig = rig_for(tmp_path / "team", offense="team", defense="team", computer=True)      # the Bengals T01, the Jets T07
    assert rig.engine.s.extras.offense_book == ["air", "pro"] and rig.engine.s.extras.defense_book == ["pro", "pro"]
    rig = rig_for(tmp_path / "style", offense="zone", defense="pressure", computer=True)
    assert rig.engine.s.extras.offense_book == ["zone", "pro"] and rig.engine.s.extras.defense_book == ["pressure", "pro"]
    rig = rig_for(tmp_path / "nonesuch", offense="wing t", defense="team")                # a value the table does not know: Classic
    assert rig.engine.s.extras.offense_book == ["classic", "classic"]


def test_the_computers_team_may_be_set_to_classic_in_team_styles_txt(tmp_path):
    rig = rig_for(tmp_path, offense="classic", computer=True)
    assert rig.engine.s.extras.offense_book[1] == "pro"
    rig = rig_for(tmp_path / "other", offense="classic", computer=True)
    teams = list(TABLE.teams)
    teams[6] = ("classic", "classic")
    rig.game.playbook_table = PB.Table(TABLE.names, TABLE.disabled, TABLE.styles, tuple(teams))
    rig.rules.books.resolve(rig.game, rig.engine.s)
    assert rig.engine.s.extras.offense_book == ["classic", "classic"] and rig.rules.books.in_use(rig.engine.s.extras) is False


# ----- the menus as data -----

def test_every_defense_group_of_every_style_fits_a_menu_of_twelve(tmp_path):
    # the offense's lists are the catalog's since SX.10c (at most ten plays and Back: test_sx10c_offense_menus.py)
    for key in D.STYLE_BY_KEY:
        rig = rig_for(tmp_path / key, offense=key, defense=key, qb_on=True, timeouts_on=True, extras={"challenges_on": True})
        for call in D.DEFENSE_FAMILIES:
            rig.rules.books.group = call
            items = items_of(rig, defense=True)
            assert 4 <= len(items) <= 12, (key, call, items)


def test_a_styles_defense_menu_is_the_six_calls_and_each_opens_its_plays(tmp_path):
    rig = rig_for(tmp_path, defense="pressure")
    assert items_of(rig, defense=True) == [" 1. Goal Line ", " 2. Short Run ", " 3. Long Run ", " 4. Blitz ", " 5. Short Pass ",
                                           " 6. Long Pass ", " 7. Save Game "]
    rig.rules.books.group = 4
    assert items_of(rig, defense=True) == [" 1. Zone Blitz ", " 2. Cover Zero Blitz ", " 3. Safety Blitz ",
                                           " 4. Linebacker Blitz ", " 5. A Gap Blitz ", " 6. Back ", " 7. Save Game "]
    assert rig.rules.defense_menu(rig.engine.s)[0].action == ("dbook", 10)


def test_classic_keeps_the_originals_menus_in_both_rules_and_a_style_with_every_play_off_does_too(tmp_path):
    rig = rig_for(tmp_path, offense="classic", defense="classic", qb_on=True)
    assert items_of(rig) == [" 1. Line Plunge ", " 2. End Run ", " 3. Screen Pass ", " 4. Short Pass ", " 5. Long Pass ",
                             " 6. Field Goal ", " 7. Punt ", " 8. Quarterback Sneak ", " 9. Quarterback Keeper ",
                             " 10. Quarterback Draw ", " 11. Save Game "]
    assert items_of(rig, defense=True)[0] == " 1. Goal Line " and len(items_of(rig, defense=True)) == 7
    rig = rig_for(tmp_path / "off")                     # SX.10c: every play of SX.7 off leaves the catalog's other plays
    rig.game.playbook_table = PB.Table(TABLE.names, frozenset(D.PLAYS), TABLE.styles, TABLE.teams)
    assert items_of(rig)[0] == " 1. Line Plunge " and items_of(rig)[7] == " 8. More Plays "


def test_a_group_with_no_play_on_is_the_originals_play_and_a_call_with_none_is_the_originals_call(tmp_path):
    rig = rig_for(tmp_path, defense="pressure")
    off = {p.id for p in D.CATALOG if p.group == 3 and p.side == "O"} | {p.id for p in D.CATALOG if p.id.startswith("D")
                                                                            and p.family == 2}
    rig.game.playbook_table = PB.Table(TABLE.names, frozenset(off), TABLE.styles, TABLE.teams)
    defense = rig.rules.defense_menu(rig.engine.s)
    assert defense[1].text == " 2. Short Run " and defense[1].action == (menus.PLAY, 2) and defense[3].action == ("dgroup", 4)


def test_the_two_point_try_menu_is_the_originals_five_items_with_classic_and_the_catalogs_with_a_playbook(tmp_path):
    rig = rig_for(tmp_path, offense="classic")
    assert rig.rules.offense_menu(rig.engine.s, True) == menus.offense_menu(True)
    rig = rig_for(tmp_path / "book")                        # SX.10c (design 2.6): the families, More Plays, Formation
    assert [i.text for i in rig.rules.offense_menu(rig.engine.s, True)][:5] == [i.text for i in menus.offense_menu(True)]


# ----- the menu loop -----

def without_items(spoken):
    """The spoken texts without the menu items (" 3. Counter "), which differ between a playbook and Classic."""
    return [t for t in spoken if not (t.startswith(" ") and t[1:2].isdigit() and ". " in t[:5])]


def test_a_classic_menu_treats_backspace_and_left_as_it_always_did(tmp_path):
    rig = rig_for(tmp_path, offense="classic", answers=[DOWN, BACKSPACE, ESCAPE])
    assert the_menu(rig) == "concede"
    assert rig.rules.menu_back(rig.engine.s) is False
    assert texts(rig)[0] == SELECT and texts(rig)[1] == " 1. Line Plunge " and texts(rig)[-1] == " 1. Line Plunge "


def test_field_goal_and_punt_are_the_originals_plays_from_the_top_menu(tmp_path):
    rig = rig_for(tmp_path, answers=["6", ENTER])          # SX.10c: the original's digits 6 and 7
    assert the_menu(rig) == "offense_chosen"
    assert rig.engine.s.offense_play == 6 and rig.rules.books.offense_id == ""
    rig = rig_for(tmp_path / "punt", answers=["7", ENTER])
    the_menu(rig)
    assert rig.engine.s.offense_play == 7


def test_the_defense_menu_opens_a_call_and_calls_one_of_its_plays(tmp_path):
    rig = nfl_engine_rig(tmp_path, answers=["4", ENTER, DOWN, ENTER],
                         rules=NflRules(timeouts_on=False, defense_book="pressure"), wisoff=2, defense=1, half=2,
                         yard_line=30, down=1, to_go=10, quarter=1)
    assert the_menu(rig, defense=True) == "defense_chosen"
    assert rig.engine.s.defense_play == 4 and rig.rules.books.defense_id == "D011"        # cover zero blitz: a Blitz
    assert texts(rig) == [SELECT_D, " 1. Goal Line ", " 4. Blitz ", SELECT_D, " 1. Zone Blitz ", " 2. Cover Zero Blitz "]


def test_a_time_out_inside_a_group_leaves_the_group_open_and_a_play_ends_the_group(tmp_path):
    rig = rig_for(tmp_path, answers=[ENTER], timeouts_on=True)
    s = rig.engine.s
    rig.rules.books.group = 1
    assert rig.rules.menu_action(s, ("back", 0)) is True and rig.rules.books.group is None
    assert rig.rules.menu_action(s, ("ogroup", 3)) is True and rig.rules.books.group == 3
    answer = rig.rules.menu_action(s, ("obook", 17))
    assert answer == (menus.PLAY, 3) and rig.rules.books.offense_id == "O017" and rig.rules.books.group is None
    assert rig.rules.menu_action(s, ("obook", 99)) is False and rig.rules.menu_action(s, ("dbook", 99)) is False


def test_an_item_of_a_group_is_spoken_in_six_words_or_fewer_and_says_its_name_as_the_player_set_it(tmp_path):
    rig = rig_for(tmp_path)
    names = dict(TABLE.names)
    names["O002"] = "Power Sweep"
    rig.game.playbook_table = PB.Table(names, TABLE.disabled, TABLE.styles, TABLE.teams)
    rig.rules.offense.menus._open("og02", "top")          # SX.10c: Power Left is the first play of Power and Gap Runs
    assert " 1. Power Sweep " in items_of(rig)
    for item in rig.rules.offense_menu(rig.engine.s, False):
        assert len(item.text.split()) <= 8                              # " 3. " and six words


# ----- the computer's choice -----

def computer_state(tmp_path, offense="air", **state):
    fields = dict(START, wisoff=2, defense=1)
    fields.update(state)
    rig = rig_for(tmp_path, computer=True, **fields)
    rig.engine.s.extras.offense_book = ["classic", offense]
    rig.engine.s.extras.defense_book = ["classic", offense]
    return rig


def candidates(key, s, percent):
    return [(p, w * percent(p.family)) for p, w in TABLE.usable(key, "O") if p.family <= 5]


def pick_of(rig, plays, pick):
    total = sum(w for _p, w in plays)
    rig.rnd.source = ScriptedRandom([Draws().below(max(total, 1), pick).values[0]], strict=True)
    rig.rnd.trace = []
    return total


def test_the_computer_draws_one_play_of_its_style_by_weight_and_situation(tmp_path):
    rig = computer_state(tmp_path, down=2, to_go=10)                    # second and ten: a long distance (8 or more)
    s = rig.engine.s
    long = T.PB_DISTANCE_PERCENT["long"]
    plays = candidates("air", s, lambda f: long.get(f, 100))
    total = pick_of(rig, plays, 0)
    s.offense_play = 3                                                  # the original's draw (any of 1 to 5), ignored
    rig.rules.computer_offense(s)
    assert rig.rnd.trace == [total] and rig.rnd.source.left == 0
    first = plays[0][0]
    assert rig.rules.books.offense_id == first.id and s.offense_play == first.family
    last = plays[-1][0]
    pick_of(rig, plays, total - 1)
    rig.rules.computer_offense(s)
    assert rig.rules.books.offense_id == last.id and s.offense_play == last.family


def test_the_percent_of_a_family_follows_distance_field_position_and_the_score_late(tmp_path):
    rig = computer_state(tmp_path, down=3, to_go=1, yard_line=50)
    s, books = rig.engine.s, rig.rules.books
    families = (1, 2, 3, 4, 5)
    short, long = T.PB_DISTANCE_PERCENT["short"], T.PB_DISTANCE_PERCENT["long"]
    assert [books.situation_percent(s, f) for f in families] == [short[f] for f in families]      # one yard to go
    s.to_go = 2
    assert [books.situation_percent(s, f) for f in families] == [short[f] for f in families]      # two is still short
    s.to_go = 5
    assert [books.situation_percent(s, f) for f in families] == [100] * 5                         # in between: no change
    s.to_go = 8
    assert [books.situation_percent(s, f) for f in families] == [long[f] for f in families]       # eight is long
    s.down = 1                                                          # first down: every drive starts at ten, no distance counts
    assert [books.situation_percent(s, f) for f in families] == [100] * 5
    s.to_go = 1
    assert [books.situation_percent(s, f) for f in families] == [100] * 5
    s.down, s.to_go = 4, 1
    assert [books.situation_percent(s, f) for f in families] == [short[f] for f in families]
    s.down, s.to_go = 3, 5
    goals = set()
    for half in (1, 2):                                                 # five yards from one goal line or from the other's
        s.half, s.yard_line = half, 5
        goals.add(to_goal(s))
        expected = T.PB_RED_ZONE_PERCENT[1] if to_goal(s) <= T.PB_RED_ZONE else 100
        assert books.situation_percent(s, 1) == expected
    assert goals == {5, 95}
    s.half, s.yard_line = 2, 50
    s.quarter, s.extras.left = 4, 200                                   # late: the fourth quarter, 3:20 left
    s.stats[2].score, s.stats[1].score = 3, 14                          # side 2 trails by 11: it needs the pass
    assert [books.situation_percent(s, f) for f in families] == [T.PB_LATE_TRAILING_PERCENT[f] for f in families]
    s.stats[2].score, s.stats[1].score = 24, 14                         # leads by 10: it runs
    assert [books.situation_percent(s, f) for f in families] == [T.PB_LATE_LEADING_PERCENT[f] for f in families]
    s.stats[2].score, s.stats[1].score = 17, 14                         # a score ahead is not enough
    assert [books.situation_percent(s, f) for f in families] == [100] * 5
    s.stats[2].score, s.stats[1].score = 3, 14
    s.extras.left = 400                                                 # not late yet
    assert [books.situation_percent(s, f) for f in families] == [100] * 5


def test_kicks_a_try_and_classic_make_no_draw_and_leave_the_play_alone(tmp_path):
    rig = computer_state(tmp_path)
    s = rig.engine.s
    for fields in (dict(offense_play=6), dict(offense_play=7), dict(offense_play=3, two_point=True)):
        for name, value in fields.items():
            setattr(s, name, value)
        rig.rnd.source = ScriptedRandom([], strict=True)
        rig.rnd.trace = []
        rig.rules.computer_offense(s)
        assert rig.rnd.trace == [] and rig.rules.books.offense_id == "" and s.offense_play == fields["offense_play"]
        s.two_point = False
    classic = computer_state(tmp_path / "classic", offense="classic")
    classic.rnd.source = ScriptedRandom([], strict=True)
    classic.rnd.trace = []
    classic.engine.s.offense_play = 4
    classic.rules.computer_offense(classic.engine.s)
    classic.rules.computer_defense(classic.engine.s)
    assert classic.rnd.trace == [] and classic.engine.s.offense_play == 4 and classic.rules.books.offense_id == ""


def test_a_quarterback_run_the_original_chose_keeps_its_family_and_a_style_play_of_it_is_called(tmp_path):
    rig = computer_state(tmp_path, offense="option", qb_on=True)
    s = rig.engine.s
    s.offense_play = 9
    plays = [(p, w) for p, w in TABLE.usable("option", "O") if p.family == 9]
    total = pick_of(rig, plays, 0)
    rig.rules.books.computer_offense(s)
    assert rig.rnd.trace == [total] and s.offense_play == 9 and rig.rules.books.offense_id == plays[0][0].id
    s.offense_play = 8                                                  # a sneak: Power Run has one, Pro Style has one
    plays = [(p, w) for p, w in TABLE.usable("option", "O") if p.family == 8]
    pick_of(rig, plays, 0)
    rig.rules.books.computer_offense(s)
    assert rig.rules.books.offense_id == plays[0][0].id


def test_the_computers_defense_picks_a_play_of_the_family_the_original_rules_chose(tmp_path):
    rig = nfl_engine_rig(tmp_path, rules=NflRules(timeouts_on=False, playbooks_on=True), wisoff=1, defense=2, half=2,
                         yard_line=30, down=1, to_go=10, quarter=1)
    s = rig.engine.s
    s.extras.defense_book = ["classic", "pressure"]
    s.defense_play = 4                                                  # a Blitz
    plays = [(p, w) for p, w in TABLE.usable("pressure", "D") if p.family == 4]
    assert [p.id for p, _w in plays] == ["D010", "D011", "D012", "D014", "D015"] and [w for _p, w in plays] == [5, 4, 4, 4, 4]
    rig.rnd.source = ScriptedRandom([Draws().below(21, 5).values[0]], strict=True)
    rig.rnd.trace = []
    rig.rules.computer_defense(s)
    assert rig.rnd.trace == [21] and rig.rules.books.defense_id == "D011" and s.defense_play == 4
    s.defense_play = 2                                                  # the family is the original's: the style's play of it
    short_run = [(i, w) for i, w in D.STYLE_BY_KEY["pressure"].defense if D.PLAYS[i].family == 2]
    assert short_run == [("D004", 3), ("D005", 4), ("D006", 2)]
    rig.rnd.source = ScriptedRandom([Draws().below(9, 3).values[0]], strict=True)
    rig.rnd.trace = []
    rig.rules.computer_defense(s)
    assert rig.rules.books.defense_id == "D005" and rig.rnd.trace == [9] and s.defense_play == 2    # 3 of 9 is past D004's 3


def defend_with_a_style(tmp_path, repeat_answer, then):
    """The computer defends against a second Line Plunge in a row (5.7): the original draws the family, a repeat is kept with
    chance 1 in 2 (rnd(2) = 1), else matched (a Line Plunge is answered by the Goal Line call)."""
    rig = nfl_engine_rig(tmp_path, rules=NflRules(timeouts_on=False, playbooks_on=True), wisoff=1, defense=2, half=2,
                         yard_line=30, down=1, to_go=10, quarter=1, offense_play=1, previous_play=1, repeats=0)
    s = rig.engine.s
    s.extras.defense_book = ["classic", "pressure"]
    d = Draws().rnd(6, 2).rnd(2, repeat_answer)
    then(d)
    rig.rnd.source = ScriptedRandom(d.values, strict=True)
    rig.rnd.trace = []
    assert rig.engine.offense_chosen() == rig.engine.snap
    assert rig.rnd.trace == d.sizes and rig.rnd.source.left == 0
    return rig


def test_the_original_rules_still_choose_the_family_and_match_a_repeated_play_before_the_style_picks(tmp_path):
    kept = defend_with_a_style(tmp_path / "kept", 1, lambda d: d.below(9, 0))         # kept: a Short Run (2), D004 of 9
    assert kept.engine.s.defense_play == 2 and kept.rules.books.defense_id == "D004"
    matched = defend_with_a_style(tmp_path / "matched", 2, lambda d: d.below(6, 5))   # matched: the Goal Line (1), D003 of 6
    assert matched.engine.s.defense_play == 1 and matched.rules.books.defense_id == "D003"
    assert [w for i, w in D.STYLE_BY_KEY["pressure"].defense if D.PLAYS[i].family == 1] == [2, 2, 2]


def test_a_call_that_was_not_run_does_not_leak_into_the_next_menu_or_the_next_kick_off(tmp_path):
    """A play can be called and never run (the period ends at the snap, a foul before the snap): the next play of a side that
    plays Classic must not read the call of the one before."""
    rig = rig_for(tmp_path, offense="classic", defense="classic")
    s, books = rig.engine.s, rig.rules.books
    books.offense_id, books.defense_id = "O002", "D011"
    rig.rules.offense_menu(s, False)
    assert books.offense_id == "" and books.defense_id == "D011"        # each menu forgets its own side's call
    rig.rules.defense_menu(s)
    assert books.defense_id == ""
    books.offense_id, books.defense_id = "O002", "D011"
    books.modifiers.arm(D.Mod(1, 1))
    rig.rules.before_kickoff(s, 1)
    assert (books.offense_id, books.defense_id, books.modifiers.mod) == ("", "", None)


# ----- what the review of SX.7 found -----

def test_a_quarterback_percent_of_zero_draws_no_keeper_or_draw_and_the_others_scale_the_chance(tmp_path):
    rig = computer_state(tmp_path, offense="option", qb_on=True, down=2, to_go=7)
    s = rig.engine.s
    for percent, one_in in ((0, None), (100, 150), (300, 50), (1000, 15), (5000, 3)):
        s.offense_play = 3
        draws = [] if one_in is None else [Draws().rnd(one_in, 1).values[0]]       # 1 is a keeper
        rig.rnd.source = ScriptedRandom(draws, strict=True)
        rig.rnd.trace = []
        rig.rules.qb.computer_offense(s, percent)
        assert rig.rnd.trace == ([] if one_in is None else [one_in]), percent
        assert s.offense_play == (3 if one_in is None else 9), percent
    s.down, s.to_go, s.offense_play = 3, 1, 3                           # the sneak on third and one does not depend on the percent
    rig.rnd.source = ScriptedRandom([Draws().rnd(2, 1).values[0]], strict=True)
    rig.rules.qb.computer_offense(s, 0)
    assert s.offense_play == 8


def test_the_try_is_the_originals_on_both_sides_of_the_ball(tmp_path):
    rig = nfl_engine_rig(tmp_path, rules=NflRules(timeouts_on=False, defense_book="pressure", playbooks_on=True), wisoff=2,
                         defense=1, half=2, yard_line=2, down=1, to_go=2, quarter=1, two_point=True)
    s, books = rig.engine.s, rig.rules.books
    assert items_of(rig, defense=True)[:2] == [" 1. Goal Line ", " 2. Short Run "]
    assert all(i.action[0] in (menus.PLAY, menus.SAVE) for i in rig.rules.defense_menu(s))        # no group, no play of a book
    books.defense_id = "D011"                                                 # a call that was somehow armed: the try ignores it
    books.arm(s, 1, 4)
    assert books.modifiers.mod is None
    s.wisoff, s.defense = 1, 2
    s.extras.defense_book = ["classic", "pressure"]
    s.defense_play = 4
    rig.rnd.source = ScriptedRandom([], strict=True)
    rig.rnd.trace = []
    rig.rules.computer_defense(s)                                             # the computer's defense draws nothing on a try
    assert rig.rnd.trace == [] and books.defense_id == ""


def test_a_kick_makes_the_computers_defense_draw_nothing(tmp_path):
    rig = nfl_engine_rig(tmp_path, rules=NflRules(timeouts_on=False, playbooks_on=True), wisoff=1, defense=2, half=2,
                         yard_line=30, down=4, to_go=3, quarter=1, offense_play=7, defense_play=2)
    rig.engine.s.extras.defense_book = ["classic", "pressure"]
    rig.rnd.source = ScriptedRandom([], strict=True)
    rig.rnd.trace = []
    rig.rules.computer_defense(rig.engine.s)
    assert rig.rnd.trace == [] and rig.rules.books.defense_id == ""


def test_on_fourth_down_the_style_only_draws_among_the_families_the_originals_go_for_it_has(tmp_path):
    rig = computer_state(tmp_path, offense="air", down=4, to_go=6)
    s = rig.engine.s
    plays = [(p, w * 100) for p, w in TABLE.usable("air", "O") if p.family <= 4]
    assert any(p.family == 5 for p, _w in TABLE.usable("air", "O"))             # Air Raid has long passes: not called here
    total = sum(w for _p, w in plays)
    for pick in range(0, total, 37):
        s.offense_play = 2
        pick_of(rig, plays, pick)
        rig.rules.computer_offense(s)
        assert 1 <= s.offense_play <= 4 and rig.rnd.trace == [total]
    s.down = 3                                                                  # the third down may call a long pass
    plays = [(p, w * 100) for p, w in TABLE.usable("air", "O") if p.family <= 5]
    pick_of(rig, plays, sum(w for _p, w in plays) - 1)
    rig.rules.computer_offense(s)
    assert s.offense_play == plays[-1][0].family


def test_the_key_0_is_the_tenth_item_and_an_item_past_the_tenth_has_no_digit(tmp_path):
    rig = rig_for(tmp_path, offense="power", qb_on=True, timeouts_on=True, answers=["0", ESCAPE])
    items = rig.rules.offense_menu(rig.engine.s, False)
    assert [i.text for i in items][9:] == [" 10. Quarterback Draw ", " 11. More Plays ", " 12. Formation and Tempo ",
                                           " 13. Time Out ", " 14. Save Game "]                  # SX.10c's menus
    assert [i.digit for i in items][9:] == [0, -1, -1, -1, -1] and items[12].letter == ""
    assert the_menu(rig) == "concede"
    assert texts(rig) == [SELECT, " 1. Line Plunge ", " 10. Quarterback Draw "]
