"""Write the two documents that are made from the game's own tables (nfl4 only, rule 0.13; CLAUDE.md 0.24 and 0.25): the Keys section of the
README draft (clone/README_keys.md, from game/key_list.py) and the plays guide (clone/PLAYS_GUIDE.md, from the description rows). A test
(tests/test_sx10b2_docs.py) fails when either file differs from what this script would write. Run from anywhere:

    py -3.14 -I C:/Users/joshk/OneDrive/dev/games/kitchensinc/nfl4/clone/tools/make_docs.py
"""
import sys
from pathlib import Path

CLONE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(CLONE / "src"))

from nfl4.extras.plays.guide import guide_text      # noqa: E402
from nfl4.game.key_list import readme_text          # noqa: E402


def main() -> int:
    for name, text in (("README_keys.md", readme_text()), ("PLAYS_GUIDE.md", guide_text())):
        (CLONE / name).write_bytes(text.encode("utf-8"))      # LF line ends, as every file of the project
        print("written %s (%d characters)" % (name, len(text)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
