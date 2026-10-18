"""PyInstaller entry point for NFL Football 4. This is inspired by Jim Kitchen.

Same as `python -m nfl4`; a separate file because PyInstaller wants a script to start from.
"""

import sys

from nfl4.app import main
from nfl4.data.lifecycle import finish

if __name__ == "__main__":
    code = 1
    try:
        code = main(sys.argv[1:])
    finally:
        finish(code)        # also when main raises: the log's last line, the state file and the process's end (7.2.1)      # flush the log and end the process at once: nothing may stay behind
