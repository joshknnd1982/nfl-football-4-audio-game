"""PyInstaller entry point for NFL Football 4. This is inspired by Jim Kitchen.

Same as `python -m nfl4`; a separate file because PyInstaller wants a script to start from.
"""

from nfl4.app import main
from nfl4.data.lifecycle import finish

if __name__ == "__main__":
    finish(main())      # flush the log and end the process at once: nothing may stay behind
