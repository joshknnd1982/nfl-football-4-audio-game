"""CHANGELOG.md for players and outside testers (rule 0.29, the owner 2026-10-23: "make a changelog markdown file with everything new, so when I give
early builds to outside testers, they know what to test"). This is inspired by Jim Kitchen.

The newest section names the program's version, the file says how to report a bug, every item of the newest build says how to test it, and the
build ships the file beside the exe (tools/build.ps1).
"""
import re
from pathlib import Path

from nfl4 import VERSION

GAME = Path(__file__).resolve().parent.parent.parent
TEXT = (GAME / "CHANGELOG.md").read_text(encoding="utf-8")


def sections():
    return re.findall(r"^## (\d+\.\d+\.\d+) \((\d{4}-\d{2}-\d{2}), (test build|release)\)$", TEXT, re.MULTILINE)


def test_the_newest_section_is_the_programs_version_and_versions_go_newest_first():
    found = sections()
    assert found and found[0][0] == VERSION, (found[:1], VERSION)
    numbers = [tuple(int(n) for n in v.split(".")) for v, _d, _k in found]
    assert numbers == sorted(numbers, reverse=True)


def test_the_file_says_how_to_report_a_bug_and_where_the_files_are():
    top = TEXT.split("\n## ", 2)[1]
    assert "Save a problem report" in top and "%APPDATA%" in top


def test_every_feature_of_the_newest_build_says_how_to_test_it():
    newest = TEXT.split("\n## " + VERSION, 1)[1].split("\n## ", 1)[0]
    features = newest.split("\n### ")[1:]
    assert features
    for block in features:
        if block.startswith("Smaller fixes"):
            continue
        assert "How to test:" in block, block[:60]


def test_the_build_ships_the_changelog_beside_the_exe():
    build = (GAME / "clone" / "tools" / "build.ps1").read_text(encoding="utf-8")
    assert '"CHANGELOG.md"' in build
