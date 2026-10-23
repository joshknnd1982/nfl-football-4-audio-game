"""The repository's README.md and its companions (P11, S11.1; CLAUDE.md 0.24 (3), section 10; nfl4 only). This is inspired by Jim Kitchen.

The README at the root of the game folder is the maintainer's own words, except the block between `<!-- keys:start -->` and `<!-- keys:end -->`,
which `clone/tools/make_docs.py` writes from the master list of keys (game/key_list.py), like README_keys.md. These tests fail when the block
differs from the list, when a key of the list is missing, when a link of the README points at a file that is not there, when a text of the
repository's front still speaks for another game (the changelog and the notice were once Brain's), or when the README claims a release that
does not exist.
"""
import re
from pathlib import Path

from nfl4.game import key_list as K

CLONE = Path(__file__).resolve().parent.parent
GAME = CLONE.parent
README = GAME / "README.md"


def readme_text() -> str:
    return README.read_bytes().decode("utf-8")


def test_the_readme_exists_with_lf_line_ends_and_the_attribution_and_the_notes():
    text = readme_text()
    assert "\r" not in text and text.endswith("\n") and text.startswith("# NFL Football 4")
    for needed in ("This is inspired by Jim Kitchen", "blind from birth", "died in 2015", "MIT License", "If something goes wrong",
                   "Madden NFL is a trademark of Electronic Arts", "If a rights holder asks for them to be removed, they will be removed",
                   "https://github.com/joshknnd1982", "no release yet"):
        assert needed.lower() in text.lower(), needed


def test_the_keys_block_is_what_the_generator_writes_and_has_every_key():
    text = readme_text()
    assert text == K.splice_readme(text)
    block = text[text.index(K.README_START):text.index(K.README_END)]
    assert block.startswith(K.README_START + "\n## Keys\n")
    for row in K.ROWS:
        assert "- **%s**" % row.keys in block and row.where in block and row.what[0].upper() + row.what[1:] in block, row.id
    assert block.count("\n- **") == len(K.ROWS)


def test_every_link_of_the_readme_points_at_a_file_that_is_in_the_repository():
    links = re.findall(r"\]\(([^)#]+)\)", readme_text())
    assert len(links) >= 10
    for link in links:
        if link.startswith("http"):
            continue
        assert (GAME / link).exists(), link


def test_the_front_of_the_repository_speaks_for_this_game_only():
    for path in (README, GAME / "CHANGELOG.md", GAME / "SOUNDS_NOTICE.txt", GAME / ".github" / "ISSUE_TEMPLATE" / "bug_report.md"):
        text = path.read_bytes().decode("utf-8")
        assert "My Brain" not in text and "Brain" not in text, path.name
    assert "NFL Football 4" in (GAME / "SOUNDS_NOTICE.txt").read_text(encoding="utf-8")
    assert (GAME / "LICENSE").read_text(encoding="utf-8").startswith("MIT License\n\nCopyright (c) 2026 Josh Kennedy")


def test_the_changelog_names_no_release_and_the_version_of_the_code_is_in_it():
    from nfl4 import VERSION
    text = (GAME / "CHANGELOG.md").read_text(encoding="utf-8")
    assert "No release has been published yet" in text and "## %s " % VERSION in text
    assert "1.0.0 (" not in text


def test_no_installer_or_archive_or_checksum_of_a_test_build_is_tracked_by_the_ignore_file():
    ignore = (GAME / ".gitignore").read_text(encoding="utf-8")
    for pattern in ("/release/*.exe", "/release/*.zip", "/release/checksums_test_*.txt", "/original/"):
        assert pattern in ignore, pattern
