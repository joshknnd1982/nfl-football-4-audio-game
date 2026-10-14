"""Run NFL Football 4: python -m nfl4 (from clone/src). This is inspired by Jim Kitchen."""
from nfl4.app import main
from nfl4.data.lifecycle import finish

if __name__ == "__main__":
    finish(main())      # flush the log and end the process at once: nothing may stay behind (playbook 7.2.1)
