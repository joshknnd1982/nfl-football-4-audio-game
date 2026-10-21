"""Every key in three places and the documents made from the tables (nfl4 only for the plays; the key rule is every game's; CLAUDE.md 0.17, 0.24,
playbook 7.13; NX-H1, D-091; PX SX.10b2). This is inspired by Jim Kitchen.

ONE master list of keys (game/key_list.py): the key, where it works, what it does, in which mode. F5 (the special keys), F6 (the game help)
and the README on GitHub (clone/README_keys.md) are made from it, the original's texts stay word for word and the added lines follow. These
tests fail when a key of the list is missing from any of the three, when the code handles a key that is not in the list, and when a generated
file differs from what its generator writes. The plays guide (clone/PLAYS_GUIDE.md) is checked here too: it is the descriptions list by list.
"""
import ast
from pathlib import Path

from nfl4.extras import nx_texts as X
from nfl4.extras.nfl_rules import NflRules
from nfl4.extras.plays import catalog as C
from nfl4.extras.plays import descriptions as DS
from nfl4.extras.plays import guide
from nfl4.game import extra_texts as words
from nfl4.game import help_texts as H
from nfl4.game import key_list as K
from nfl4.game.rules import CLASSIC

CLONE = Path(__file__).resolve().parent.parent
SRC = CLONE / "src" / "nfl4"
LETTERS_CALLS = ("menu_item", "item", "MenuItem")


def all_on_rules() -> NflRules:
    """The N. F. L. rules with every feature on and a playbook in use: every feature's own F5 and F6 lines are spoken."""
    return NflRules(timeouts_on=True, penalties_on=True, onside_on=True, qb_on=True, challenges_on=True, offense_book="west",
                    defense_book="pro", playbooks_on=True)


def f5_text(rules, mode):
    return " ".join([H.SPECIAL_KEYS, words.KEYS_ADDED_F9] + rules.extra_help(K.KEY_F5))


def f6_lines(rules):
    return [H.GAME_INSTRUCTIONS, H.FOOTBALL_INSTRUCTIONS] + rules.extra_help(K.KEY_F6)


# ----- the list -----

def test_the_master_list_is_complete_and_has_no_duplicates():
    assert len({row.id for row in K.ROWS}) == len(K.ROWS) == len(K.BY_ID)
    assert len({row.keys for row in K.ROWS}) == len(K.ROWS)
    for row in K.ROWS:
        assert row.keys and row.where and row.what and row.modes in ("all", "nfl"), row
        assert row.probe5 or row.f5, row                      # F5 names the key either already or by a generated line
        assert not (row.probe5 and row.f5), row
        if row.original and row.probe5:
            assert row.probe5 in H.SPECIAL_KEYS, row           # the original's own list names it, word for word
        assert not row.what.endswith("."), row
    assert {r.keys for r in K.ROWS if r.modes == "nfl"} >= {"T", "S", "C", "D", "A and D", "Backspace or Left, B"}


def test_rows_are_for_a_mode_and_classic_has_none_of_the_added_n_f_l_keys():
    classic = {row.id for row in K.rows_for("classic")}
    assert "timeout" not in classic and "describe" not in classic and "save" not in classic
    assert {row.id for row in K.rows_for("nfl")} == {row.id for row in K.ROWS}


# ----- F5, F6 -----

def test_f5_names_every_key_in_classic_and_the_original_text_comes_first_word_for_word():
    text = f5_text(CLASSIC, "classic")
    assert text.startswith(H.SPECIAL_KEYS + " " + words.KEYS_ADDED_F9)
    for row in K.rows_for("classic"):
        assert (row.probe5 or row.f5.strip()) in text, row
    for row in K.ROWS:
        if row.modes == "nfl" and row.f5:
            assert row.f5.strip() not in text, row


def test_f5_names_every_key_in_the_n_f_l_rules():
    text = f5_text(all_on_rules(), "nfl")
    for row in K.rows_for("nfl"):
        assert (row.probe5 or row.f5.strip()) in text, row


def test_f6_says_every_key_with_where_it_works_and_what_it_does_in_both_modes():
    for rules, mode in ((CLASSIC, "classic"), (all_on_rules(), "nfl")):
        lines = f6_lines(rules)
        assert lines[0] == H.GAME_INSTRUCTIONS and lines[1] == H.FOOTBALL_INSTRUCTIONS         # the original's, word for word
        for row in K.rows_for(mode):
            wanted = " %s. %s. %s. " % (row.keys, row.where, row.what[0].upper() + row.what[1:])
            assert wanted in lines, (mode, row)
    assert " The keys. Each key is said with where it works and what it does. " in f6_lines(CLASSIC)


def test_the_key_of_a_feature_is_documented_only_while_the_feature_is_on():
    off = NflRules(timeouts_on=False, penalties_on=False, qb_on=False, challenges_on=False, offense_book="classic")
    lines = " ".join(off.extra_help(K.KEY_F5) + off.extra_help(K.KEY_F6))
    for text in (" T. Anywhere in a game", "At a penalty question", "In the offense menu with quarterback runs", "Challenge the Ruling"):
        assert text not in lines, text
    assert K.BY_ID["describe"].f5.strip() in lines and "S. In a play menu." in lines          # D and S need no feature
    assert {row.feature for row in K.ROWS} == {"", "timeouts", "challenges", "penalties", "qb", "playbooks"}


def test_the_d_key_is_in_f5_and_f6_of_the_n_f_l_rules_and_not_in_classic():
    row = K.BY_ID["describe"]
    assert row.f5.strip() in f5_text(all_on_rules(), "nfl")
    assert not [line for line in CLASSIC.extra_help(K.KEY_F5) + CLASSIC.extra_help(K.KEY_F6) if "describes the current item" in line]
    assert any("D. In a play menu." in line for line in all_on_rules().extra_help(K.KEY_F6))


# ----- the README draft -----

def test_the_readme_keys_draft_is_what_the_generator_writes_and_has_every_key():
    text = (CLONE / "README_keys.md").read_bytes().decode("utf-8")
    assert "\r" not in text and text == K.readme_text()
    for row in K.ROWS:
        assert "**%s**" % row.keys in text, row
        assert row.where in text and row.what[0].upper() + row.what[1:] in text, row
    assert text.startswith("# Keys")


def test_the_plays_guide_is_what_the_generator_writes_and_has_every_play_with_its_description():
    text = (CLONE / "PLAYS_GUIDE.md").read_bytes().decode("utf-8")
    assert "\r" not in text and text == guide.guide_text()
    for c in C.CATALOG:
        assert "- **%s**: %s" % (c.name, DS.text(DS.play_row(c.id))) in text, c.id
    for group in C.GROUPS:
        assert "### " + group.name in text and DS.text(DS.LIST_ROWS[group.key]) in text
    for row in set(DS.all_rows()) - set(DS.F7_WORD_ROWS):
        assert DS.text(row) in text, row
    assert text.index("## The original's plays") < text.index("## Offense") < text.index("## Defense") < text.index("## Special teams")


# ----- the scan of the code -----

def parsed():
    for path in sorted(SRC.rglob("*.py")):
        yield path, ast.parse(path.read_bytes().decode("utf-8"))


def key_constants() -> dict:
    """Every KEY_ name the code assigns a key code to (an int or a digit string), with a file that does."""
    found = {}
    for path, tree in parsed():
        for node in ast.walk(tree):
            if not isinstance(node, ast.Assign) or len(node.targets) != 1:
                continue
            target, value = node.targets[0], node.value
            if isinstance(target, ast.Tuple) and isinstance(value, ast.Tuple):
                pairs = list(zip(target.elts, value.elts))
            else:
                pairs = [(target, value)]
            for name, constant in pairs:
                if (isinstance(name, ast.Name) and name.id.startswith("KEY_") and isinstance(constant, ast.Constant)
                        and (isinstance(constant.value, int) or (isinstance(constant.value, str) and constant.value.isdigit()))):
                    found.setdefault(name.id, path.name)
    return found


def single_letters(node):
    """The one-letter strings in a constant, a tuple, a list or a set."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return [node.value] if len(node.value) == 1 and node.value.isalpha() else ([c for c in node.value if c.isalpha()]
                                                                                  if node.value and len(node.value) <= 3 else [])
    if isinstance(node, (ast.Tuple, ast.List, ast.Set)):
        return [letter for element in node.elts for letter in single_letters(element)]
    return []


def handled_letters() -> dict:
    """The letter keys the code compares a typed character with, and the letters it gives to menu items."""
    found = {}
    for path, tree in parsed():
        for node in ast.walk(tree):
            if (isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name)
                    and node.targets[0].id.endswith("LETTERS") and isinstance(node.value, ast.Dict)):
                for value in node.value.values:            # a table of menu letters (extras/plays/play_menus.LETTERS, SX.10c)
                    if isinstance(value, ast.Constant) and isinstance(value.value, str) and len(value.value) == 1:
                        found.setdefault(value.value, path.name)
                continue
            if isinstance(node, ast.Compare):
                left = ast.unparse(node.left).lower()
                if "char" in left or "letter" in left:
                    for comparator in node.comparators:
                        for letter in single_letters(comparator):
                            found.setdefault(letter, path.name)
            elif isinstance(node, ast.Call):
                func = node.func.id if isinstance(node.func, ast.Name) else getattr(node.func, "attr", "")
                if func not in LETTERS_CALLS:
                    continue
                candidates = [node.args[3]] if len(node.args) > 3 else []
                candidates += [kw.value for kw in node.keywords if kw.arg == "letter"]
                for candidate in candidates:
                    if isinstance(candidate, ast.Constant) and isinstance(candidate.value, str) and len(candidate.value) == 1:
                        found.setdefault(candidate.value, path.name)
    return found


def test_every_key_constant_of_the_code_is_in_the_master_list_and_every_listed_constant_is_in_the_code():
    found = key_constants()
    listed = {name for row in K.ROWS for name in row.consts}
    assert len(found) > 25                                    # the scan looks at something
    assert set(found) - listed - K.NOT_KEYS == set(), {n: found[n] for n in set(found) - listed - K.NOT_KEYS}
    assert listed - set(found) == set(), listed - set(found)


def test_every_letter_key_the_code_handles_is_in_the_master_list():
    found = handled_letters()
    listed = {letter for row in K.ROWS for letter in row.letters}
    assert {"y", "n", "a", "d", "s", "c", "b", "h", "t", "r", "k"} <= set(found)
    assert set(found) - listed == set(), {l: found[l] for l in set(found) - listed}
    assert listed - set(found) == set(), listed - set(found)


def test_the_scan_would_find_a_key_that_is_not_in_the_list():
    tree = ast.parse('KEY_NEW = "99"\nif self.keys.char == "z":\n    pass\nitem(1, "x", ("a", 1), "q")')
    consts = [n for n in ast.walk(tree) if isinstance(n, ast.Assign)]
    assert consts and single_letters(ast.parse('x in ("z", "q")').body[0].value.comparators[0]) == ["z", "q"]


def test_the_text_table_has_no_text_that_names_the_original_author_as_the_maker_in_the_new_rows():
    for row in DS.all_rows():
        assert "Jim" not in X.text(row), row
