"""Every text of the start-up, the week loop, the main menu and the exit is a string of the original's exe. This is inspired by Jim Kitchen.

game/program_texts.py (typed from the lifted Form_Load, p_486990, S7.4b) and the title, thank-you and "no game menu" sentences
of game/texts.py, each checked against spec/strings_all.tsv, with the procedure that owns the string; the clone's own sentences
are listed here and must NOT be in the exe (B-T40: no name of the module is assigned twice).
"""
import ast
import collections

from nfl4.game import program_texts as P
from nfl4.game import texts
from test_prompt_texts import module_texts
from specfiles import original_strings, strings_table

CLONE_ONLY = {"SEASON_OVER", "FIRST_START_F9"}


def owners():
    rows = {}
    for row in strings_table():
        rows.setdefault(row["text"], set()).update(p for p in row["procedures"].split(",") if p)
    return rows


def test_every_text_of_form_load_is_a_string_of_the_original_except_the_clones_own():
    strings, texts_of_module = original_strings(), module_texts(P)
    assert sorted(set(texts_of_module) - {n for n, t in texts_of_module.items() if t in strings}) == sorted(CLONE_ONLY)
    for name in CLONE_ONLY:
        assert getattr(P, name) not in strings                         # a text of the clone is not mistaken for the original's
    assert len(texts_of_module) == 11


def test_the_menu_choices_and_the_week_names_are_form_loads_own_strings():
    rows = owners()
    for text in list(P.CHOICES.values()) + [P.WELCOME_TO, P.THIS_IS_WEEK, P.THIS_IS_WEEK_LOG, P.THIS_IS_THE, P.TODAYS_GAME_IS,
                                            P.OF_JIMS_FOOTBALL, P.SELECT, P.AND]:
        assert "p_486990" in rows[text], text
    assert [t for t in P.CHOICES.values()] == [" 1. play game ", " 2. see schedule ", " 3. see standings ", " 4. exit game "]


def test_the_exit_texts_are_form_loads_and_the_title_is_the_clones_rule_0_5_1():
    rows = owners()
    assert "p_486990" in rows[texts.THANK_YOU] and "p_486990" in rows[texts.NO_GAME_MENU.strip()]
    assert texts.TITLE_SPOKEN not in original_strings() and P.LOG_TITLE_ORIGINAL in original_strings()


def test_no_name_of_the_module_is_assigned_twice():
    tree = ast.parse(open(P.__file__, encoding="utf-8").read())
    names = collections.Counter(n.id for node in tree.body if isinstance(node, ast.Assign)
                                for target in node.targets for n in ast.walk(target) if isinstance(n, ast.Name))
    assert [name for name, count in names.items() if count > 1] == []
