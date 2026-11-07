"""CHANGELOG.md for players and outside testers (rule 0.29, the owner 2026-10-23: "make a changelog markdown file with everything new, so when I give
early builds to outside testers, they know what to test"). This is inspired by Jim Kitchen.

The newest section names the program's version, the file says how to report a bug, every item of the newest build says how to test it, and the
build ships the file beside the exe (tools/build.ps1).
"""
import re

import pytest
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
    build = (GAME / "game" / "tools" / "build.ps1").read_text(encoding="utf-8")
    assert '"CHANGELOG.md"' in build


# Rule 0.39 (the owner 2026-11-06: "like my NVDA addons, I want all of my games ... to produce a changelog by default which is put on my
# github so everyone knows changes that have been made"): the file passes game\tools\release_notes.py's check, the README links it and the
# Releases page, and a release's notes carry the version's whole section, as an NVDA add-on's release does.
import importlib.util
import sys

TOOL = GAME / "game" / "tools" / "release_notes.py"
_spec = importlib.util.spec_from_file_location("release_notes", TOOL)
notes_tool = importlib.util.module_from_spec(_spec)
sys.modules["release_notes"] = notes_tool
_spec.loader.exec_module(notes_tool)


def test_the_changelog_passes_the_check_of_rule_0_39():
    assert notes_tool.problems(GAME, VERSION) == []
    assert len((GAME / "CHANGELOG.md").read_bytes()) < notes_tool.LIMIT


def test_the_older_versions_are_linked_and_nothing_of_them_was_lost():
    older = TEXT.split(notes_tool.OLDER, 1)[1]
    archives = sorted((GAME / "changelog").glob("CHANGELOG-*.md"))
    assert archives
    every = TEXT.split(notes_tool.OLDER, 1)[0] + "".join(path.read_text(encoding="utf-8") for path in archives)
    versions = re.findall(r"^## (\d+\.\d+\.\d+) \(", every, re.MULTILINE)
    assert len(versions) == len(set(versions)) and "0.9.0" in versions and VERSION in versions
    for path in archives:
        assert "https://github.com/joshknnd1982/nfl-football-4-audio-game/blob/master/changelog/" + path.name in older
        assert "](../CHANGELOG.md)" in path.read_text(encoding="utf-8")


def test_the_readme_links_the_changelog_and_the_releases_and_names_no_version_that_goes_stale():
    readme = (GAME / "README.md").read_text(encoding="utf-8")
    top = readme.split("\n## ", 1)[0]
    assert "](CHANGELOG.md)" in top and "](https://github.com/joshknnd1982/nfl-football-4-audio-game/releases)" in top
    assert not re.search(r"\b\d+\.\d+\.\d+\b", top), "the README's top names a version, which goes stale at the next build"


def test_the_release_notes_carry_the_versions_whole_section_word_for_word(tmp_path):
    block = notes_tool.section(TEXT, VERSION)
    assert block.startswith("## %s (" % VERSION) and "How to test:" in block
    plain = notes_tool.notes(VERSION, GAME, repo="joshknnd1982/nfl-football-4-audio-game", branch="master")
    assert plain.startswith(block.rstrip("\n"))
    assert "https://github.com/joshknnd1982/nfl-football-4-audio-game/blob/master/CHANGELOG.md" in plain
    template = tmp_path / "template.md"
    template.write_bytes("Intro {version}.\n\n{changelog}\n\nSHA-256 {sha256}. All: {changelog_url} {releases_url}\n".encode("utf-8"))
    installer = tmp_path / "setup.exe"
    installer.write_bytes(b"abc")
    filled = notes_tool.notes(VERSION, GAME, str(template), str(installer), "joshknnd1982/nfl-football-4-audio-game", "master")
    assert filled.startswith("Intro %s.\n\n%s" % (VERSION, block.rstrip("\n")))
    assert "BA7816BF8F01CFEA414140DE5DAE2223B00361A396177A9CB410FF61F20015AD" in filled and "{" not in filled.replace(block, "")
    with pytest.raises(SystemExit):
        notes_tool.notes("0.0.1", GAME, repo="a/b", branch="master")
    with pytest.raises(SystemExit):                                     # a {sha256} with no installer is refused
        notes_tool.notes(VERSION, GAME, str(template), None, "a/b", "master")


def test_the_archive_moves_only_whole_sections_and_keeps_every_word(tmp_path):
    parts = ["# Changelog\n\n## Before you start\n\n- Save a problem report. %APPDATA%\n\n"]
    for minor in range(40, 0, -1):
        parts.append("## 0.%d.0 (2026-10-%02d, test build)\n\n### Item %d\n%s\n\n**How to test:** press F1.\n\n"
                     % (minor, minor % 28 + 1, minor, "words " * 400))
    (tmp_path / "CHANGELOG.md").write_bytes("".join(parts).encode("utf-8"))   # LF, as every markdown file here
    before = notes_tool.split_sections("".join(parts))[1]
    written = notes_tool.archive(tmp_path, "a/b", "master")
    assert written and len((tmp_path / "CHANGELOG.md").read_bytes()) < notes_tool.KEEP
    assert notes_tool.problems(tmp_path, "0.40.0") == []
    after = notes_tool.split_sections((tmp_path / "CHANGELOG.md").read_text(encoding="utf-8"))[1]
    for path in sorted(written, key=lambda p: p.name, reverse=True):
        after += notes_tool.split_sections(path.read_text(encoding="utf-8"))[1]
    assert sorted((n, b.rstrip("\n")) for n, b in after) == sorted((n, b.rstrip("\n")) for n, b in before)
    assert notes_tool.archive(tmp_path, "a/b", "master") == []          # under the limit now: nothing moves


# Issue 5 (a tester, 2026-11-07: "A change log needs to be included with every release so we know what to test for and what has been
# changed."): every release carries its section in its notes and the whole changelog of that version as the asset CHANGELOG-<version>.md,
# and the installed game has a Start menu entry that opens the file.

def test_the_full_changelog_of_a_version_has_it_and_every_older_version_word_for_word():
    prefix, every = notes_tool.every_section(GAME)
    names = [name for name, _b in every]
    assert names[0] == VERSION and "0.9.0" in names and len(names) == len(set(names))
    full = notes_tool.full_changelog(VERSION, GAME)
    assert "Save a problem report" in full and "%APPDATA%" in full
    for name, block in every:
        assert block.rstrip("\n") in full, name
    older = notes_tool.full_changelog("0.16.2", GAME)
    assert "\n## 0.16.2 (" in older and "\n## 0.9.0 (" in older and "\n## 0.16.3 (" not in older
    with pytest.raises(SystemExit):
        notes_tool.full_changelog("0.16.7", GAME)                       # never built: no section, refused
    assert notes_tool.asset_name("0.16.19") == "CHANGELOG-0.16.19.md"


def test_a_release_without_its_section_or_its_changelog_file_is_caught_and_mended():
    block = notes_tool.section(TEXT, VERSION)
    good = "Intro.\n\n" + block.replace("\n", "\r\n") + "\nInstall: run it."
    asset = notes_tool.asset_name(VERSION)
    assert notes_tool.release_body_problems(VERSION, good, ["setup.exe", asset], False, block) == []
    old = "**Title**\n\nAbout the game.\n\nWhat is new in this build (short):\n- a thing\n\nInstall: run it.\n\nLicense."
    found = notes_tool.release_body_problems(VERSION, old, ["setup.exe"], True, block)
    assert len(found) == 3
    mended = notes_tool.mended_body(old, VERSION, block, "URL")
    assert mended.startswith("**Title**\n\nAbout the game.\n\nWhat is new in this build, word for word")
    assert block.rstrip("\n") in mended and "- a thing" not in mended and mended.endswith("Install: run it.\n\nLicense.")
    assert notes_tool.release_body_problems(VERSION, mended, [asset], False, block) == []
    assert notes_tool.mended_body(mended, VERSION, block, "URL") == mended            # mending twice changes nothing
    plain = notes_tool.mended_body("**Title**\n\nAbout.\n\nLicense.", VERSION, block, "URL")
    assert plain.startswith("**Title**\n\nAbout.\n\nWhat is new") and plain.endswith("License.")


def test_the_installer_has_a_start_menu_entry_that_opens_the_changelog():
    script = (GAME / "release" / "installer.iss").read_text(encoding="utf-8")
    assert r'Name: "{group}\NFL Football 4 changelog, what is new"; Filename: "{win}\notepad.exe"; Parameters: """{app}\CHANGELOG.md"""' in script
    check = (GAME / "game" / "tools" / "verify_installer.py").read_text(encoding="utf-8")
    assert "NFL Football 4 changelog, what is new.lnk" in check
