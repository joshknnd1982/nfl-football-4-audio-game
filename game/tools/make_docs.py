"""Write the documents that are made from the game's own tables (nfl4 only, rule 0.13; CLAUDE.md 0.24 and 0.25): the Keys section of the
README (game/README_keys.md, and the block between the markers `<!-- keys:start -->` and `<!-- keys:end -->` of README.md in the game folder,
both from game/key_list.py) and the plays guide (game/PLAYS_GUIDE.md, from the description rows). Tests (tests/test_sx10b2_keys.py,
tests/test_p11_readme.py) fail when a file differs from what this script would write. Run from anywhere:

    py -3.14 -I C:/Users/joshk/OneDrive/dev/games/kitchensinc/nfl4/game/tools/make_docs.py
"""
import sys
from pathlib import Path

CODE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(CODE / "src"))

from nfl4.extras.plays.guide import guide_text      # noqa: E402
from nfl4.game.key_list import readme_text, splice_readme      # noqa: E402


def main() -> int:
    for name, text in (("README_keys.md", readme_text()), ("PLAYS_GUIDE.md", guide_text())):
        (CODE / name).write_bytes(text.encode("utf-8"))      # LF line ends, as every file of the project
        print("written %s (%d characters)" % (name, len(text)))
    readme = CODE.parent / "README.md"                      # the repository's README: only the block between the markers is rewritten
    if readme.exists():
        text = splice_readme(readme.read_bytes().decode("utf-8"))
        readme.write_bytes(text.encode("utf-8"))
        print("written README.md (%d characters)" % len(text))
    return 0


if __name__ == "__main__":
    sys.exit(main())
