"""More plays on defense are found, and "the playbook's choice" is explained (nfl4 only, rule 0.13; CLAUDE.md 0.28; SZ.5, D-110). This is inspired by Jim Kitchen.

A player's e-mail (2026-10-22): "Pick more plays on defense. No other plays are listed that I see." and "It says recommended formations but you don't see any
recommended play. Is this an oversight? If not, tell the user at least once during game play." On defense the six calls were all the menu showed and the
other 89 were behind Right on a call (nothing said so), and More Plays held only the situation defenses; Formation and Tempo said "the playbook's
choice" and never what that means. Now More Plays on defense holds every list of calls, the menus say once, in the first three program runs, where Right and M are
and that Enter lets the playbook pick, and the settings list says that nothing is recommended. No draw is made: a strict scripted source fails the test on one.
"""
from nfl4.data import settingsfile
from nfl4.data.settings import Settings
from nfl4.extras import nx_texts as X
from nfl4.extras.nfl_rules import NflRules
from nfl4.extras.plays import catalog as C
from nfl4.extras.plays import descriptions as DS
from nfl4.extras.plays import play_menus as PM
from nfl4.game.rules import CLASSIC, ClassicRules
from nflrig import nfl_engine_rig
from pagrig import Draws, run_steps

ENTER, ESCAPE, RIGHT = 13, 27, 39
MENU_UNTIL = ("offense_chosen", "defense_chosen", "concede", "save_game")
DEFENSE = dict(wisoff=2, defense=1, half=2, yard_line=30, down=1, to_go=10, quarter=1)
OFFENSE = dict(wisoff=1, defense=2, half=2, yard_line=30, down=1, to_go=10, quarter=1)


def rig_for(tmp_path, answers, hints=0, rules=None, **state):
    fields = dict(DEFENSE)
    fields.update(state)
    rules = rules or NflRules(timeouts_on=False, offense_book="pro", defense_book="pro")
    rig = nfl_engine_rig(tmp_path, answers=list(answers), rules=rules, **fields)
    rig.game.options.settings.game.nx_menu_hints = hints
    return rig


def texts(rig, start=0):
    return [t for t, _, _ in rig.said[start:]]


def defense_menu(rig):
    return run_steps(rig, rig.engine.defense_menu, Draws(), until=MENU_UNTIL)


def offense_menu(rig):
    return run_steps(rig, rig.engine.offense_menu, Draws(), until=MENU_UNTIL)


# ----- More Plays on defense -----

def test_more_plays_on_defense_holds_every_list_of_calls_and_the_kick_defense():
    keys = PM.more_groups("D")
    assert len(keys) == len(set(keys)) == 12 and keys[:2] == ["dg11", "kg04"]          # where they always were (keys 1 and 2)
    defense_groups = [g for g in C.GROUPS if g.side == "D"]
    assert set(keys[1:]) | {"dg11"} == {g.key for g in defense_groups} | {"kg04"}
    # the lists Right opens from the six calls follow, in the order Right goes through them
    assert keys[2:] == [g.key for g in sorted((g for g in defense_groups if g.family), key=lambda g: (g.family, g.order))]
    context = PM.Context(side="D")
    seen = set()
    for key in keys:
        seen |= {c.id for c in PM.concepts_of(key, context)}
    every_call = {c.id for c in C.CATALOG if c.side == "D"}
    assert every_call <= seen and len(every_call) >= 89
    assert PM.more_groups("O") == [g.key for g in C.GROUPS if g.side == "O" and g.family == 0]          # the offense's did not change


def test_the_more_plays_menu_of_the_defense_lists_them_with_find_and_back():
    menus = PM.PlayMenus(PM.Context(side="D"))
    top = menus.items()
    more = next(i for i in top if i.action[0] == PM.MORE)
    assert menus.enter(more) is True and menus.level == PM.MORE_LEVEL
    items = menus.items()
    assert len(items) == 12 + 2 and items[-2].action == (PM.FIND, 0) and items[-1].action == (PM.BACK, 0)
    assert [i.action[1] for i in items[:-2]] == PM.more_groups("D")


def test_the_description_of_more_plays_is_the_defenses_own():
    assert DS.menu_item_row("D", ("more", 0)) == "NXB-G09" and DS.menu_item_row("O", ("more", 0)) == "NXB-E18"
    assert "defensive calls" in X.TEXTS["NXB-G09"] and "NXB-G09" in DS.all_rows()


def test_the_real_menu_of_the_defense_opens_more_plays_with_the_m_key(tmp_path):
    rig = rig_for(tmp_path, ["m", ENTER, 40, ESCAPE], hints=3)
    assert defense_menu(rig) == "concede"
    said = texts(rig)
    first, second = PM.more_groups("D")[:2]
    for key in (first, second):
        assert any(X.TEXTS[C.group_text_id(C.GROUP_BY_KEY[key])].strip() in t for t in said), key


# ----- the hints -----

def test_the_first_defense_menu_says_where_the_other_calls_are_once_and_counts_the_run(tmp_path):
    rig = rig_for(tmp_path, [ESCAPE])
    assert defense_menu(rig) == "concede"
    said = texts(rig)
    assert said.count(X.TEXTS["NXB-H18"]) == 1 and said.index(X.TEXTS["NXB-H18"]) == said.index(" 1. Goal Line ") + 1
    assert rig.game.options.settings.game.nx_menu_hints == 1
    assert rig.rules.menu_hint(rig.engine.s) == "" and rig.game.options.settings.game.nx_menu_hints == 1    # not again in the same program run


def test_the_offense_menu_has_its_own_hint(tmp_path):
    rig = rig_for(tmp_path, [ESCAPE], **OFFENSE)
    assert offense_menu(rig) == "concede"
    said = texts(rig)
    assert said.count(X.TEXTS["NXB-H17"]) == 1 and "Right opens more plays" in X.TEXTS["NXB-H17"] and "M opens More Plays" in X.TEXTS["NXB-H17"]


def test_the_hints_stop_after_three_runs_and_when_the_player_has_found_the_lists(tmp_path):
    rig = rig_for(tmp_path / "three", [ESCAPE], hints=3)
    defense_menu(rig)
    assert X.TEXTS["NXB-H18"] not in texts(rig) and rig.game.options.settings.game.nx_menu_hints == 3
    rig = rig_for(tmp_path / "right", [RIGHT, ESCAPE])
    defense_menu(rig)
    assert rig.game.options.settings.game.nx_menu_hints == 3                     # Right opened a list: he knows
    rig = rig_for(tmp_path / "more", ["m", ENTER, ESCAPE])
    defense_menu(rig)
    assert rig.game.options.settings.game.nx_menu_hints == 3


def test_the_settings_list_says_the_playbooks_choice_is_no_recommendation(tmp_path):
    rig = rig_for(tmp_path, ["o", ENTER, ESCAPE], **OFFENSE)
    offense_menu(rig)
    said = texts(rig)
    assert said.count(X.TEXTS["NXB-H19"]) == 1
    assert "recommends nothing" in X.TEXTS["NXB-H19"] and "the playbook's choice" in X.TEXTS["NXB-H19"]
    assert said.index(X.TEXTS["NXB-H19"]) > said.index(X.text("NXB-54")) if X.text("NXB-54") in said else True


def test_classic_and_a_hand_made_rules_object_say_no_hint(tmp_path):
    assert CLASSIC.menu_hint(None) == "" and ClassicRules().menu_hint(object()) == ""
    rig = rig_for(tmp_path, [ESCAPE], rules=NflRules(timeouts_on=False, offense_book="classic", defense_book="classic"))
    defense_menu(rig)
    assert not [t for t in texts(rig) if t in (X.TEXTS["NXB-H17"], X.TEXTS["NXB-H18"], X.TEXTS["NXB-H19"])]


def test_the_hint_texts_are_plain_and_short_and_name_the_keys():
    for text_id in ("NXB-H17", "NXB-H18", "NXB-H19", "NXB-G09"):
        assert text_id in X.TEXTS and len(X.TEXTS[text_id]) <= 200
    assert "Enter on a call lets the playbook pick" in X.TEXTS["NXB-H18"] and "M opens More Plays" in X.TEXTS["NXB-H18"]
    assert "Right on a call opens its lists, and M opens every list" in X.TEXTS["NXH-57"]
    assert "Enter on a play type lets the playbook pick the play. Right opens its lists, M opens More Plays" in X.TEXTS["NXH-27"]       # SZ.7, D-113


def test_the_setting_is_saved_and_read_back():
    settings = Settings.defaults()
    assert settings.game.nx_menu_hints == 0
    settings.game.nx_menu_hints = 2
    again, problems = settingsfile.parse(settingsfile.render(settings))
    assert again.game.nx_menu_hints == 2 and problems == []
    old, problems = settingsfile.parse(settingsfile.render(settings).replace("nx_menu_hints = 2\n", ""))
    assert old.game.nx_menu_hints == 0 and problems == []
