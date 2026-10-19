"""The About text of the extras and the Franchise with the trademark notice (nfl4 only, rule 0.13; NFL_EXTRA_FEATURES NX-R6; PX SX.9). This is
inspired by Jim Kitchen.

NX-R6: the README and the About item say that the playbooks and the franchise are inspired by the ideas of Madden NFL, that Madden NFL is a
trademark of Electronic Arts, and that the project is not made, endorsed or supported by EA or the NFL. Nothing else the game says or
writes names Madden or Electronic Arts: every string of the program's code (not its comments or docstrings) is read here.
"""
import ast
from pathlib import Path

from nfl4.extras import nx_texts as X
from nfl4.game import extra_texts as words

SRC = Path(__file__).resolve().parent.parent / "src" / "nfl4"
NAMES = ("madden", "electronic arts")


def test_the_about_text_has_the_notice_and_names_the_added_rules():
    text = " ".join(words.ABOUT_LINES)
    assert "inspired by the playbooks and franchise ideas of Madden N. F. L." in text
    assert "Madden N. F. L. is a trademark of Electronic Arts." in text
    assert "not made, endorsed or supported by Electronic Arts or the N. F. L." in text
    assert "N. F. L. rules" in text and "franchise" in text and "Classic" in text
    assert words.ABOUT_LINES[1].startswith("This is inspired by Jim Kitchen.")       # rule 0.5 stays as it was


def _strings(path: Path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    docs = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node.body:
            first = node.body[0]
            if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant):
                docs.add(id(first.value))
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in docs:
            yield node.value


def test_no_other_text_of_the_game_names_madden_or_electronic_arts():
    found = []
    for path in sorted(SRC.rglob("*.py")):
        for value in _strings(path):
            if any(name in value.lower() for name in NAMES) and value not in "".join(words.ABOUT_LINES):
                found.append((path.name, value[:80]))
    assert found == []
    assert not any(name in t.lower() for t in X.TEXTS.values() for name in NAMES)


def test_the_f9_help_counts_the_franchise_item():
    assert "five items" in words.F9_HELP and "six items" in words.F9_HELP_FRANCHISE
    assert "franchise" in words.F9_HELP_FRANCHISE and "franchise" not in words.F9_HELP


def test_f1_in_the_f9_menu_says_six_items_with_the_franchise_and_five_without(tmp_path):
    from frrig import ESC, F1, F9, franchise_rig, quit_policy, run_until, spoken
    from programrig import preset_season
    rig = franchise_rig(tmp_path / "nfl", [F9, F1, ESC], preset=preset_season(), policy=quit_policy)
    run_until(rig)
    assert words.F9_HELP_FRANCHISE in spoken(rig) and words.F9_HELP not in spoken(rig)
    rig = franchise_rig(tmp_path / "classic", [F9, F1, ESC], nfl=False, preset=preset_season(), policy=quit_policy)
    run_until(rig)
    assert words.F9_HELP in spoken(rig) and words.F9_HELP_FRANCHISE not in spoken(rig)
