"""A rig for the start-up choice and the saved games (SX.14, CLAUDE.md 0.23): real `SavedGame` records with their summary, a program rig with the
choice switched ON, and the helpers the tests of NX-S1 to NX-S8 share. This is inspired by Jim Kitchen.

`menu_rig` builds the rig of tests/programrig.py (the Game on the virtual clock, a stand-in for pag, the memory store) with
`rig.game.startup_menu = True`, so the program asks what to do with what is saved; put saves in `rig.store.shelf` (slots 1 to 3 and the
automatic save) before `rig.run()`. A test with no keys left makes the first wait raise AssertionError: that is how the tests prove that nothing
is loaded, deleted or replaced without a key.
"""
import json

from nfl4.game.gamestate import SavedGame, SideStats
from programrig import DOWN, ENTER, UP, program_rig, saved_game, played, preset_season  # noqa: F401 (re-exported)

EXIT = [DOWN, DOWN, DOWN, ENTER]          # the main menu's "exit game"


def info(own="Bengals", opp="Jets", week=1, left=6, seconds=None, **more):
    values = {"v": 1, "week": week, "kind": "classic", "rules": "classic", "own": own, "opp": opp, "lm": left, "ls": seconds}
    values.update(more)
    return json.dumps(values)


def a_saved(own=14, opponent=10, quarter=3, wisoff=1, week=1, with_info=True, **fields):
    """A saved game of the Bengals (side 1) against the Jets: 14 to 10 in the third quarter, the Bengals with the ball."""
    stats = {1: SideStats(score=own), 2: SideStats(score=opponent)}
    return SavedGame(wisoff, 3 - wisoff, 2, quarter, 12, [31, 32, 33, 34, 35], 71.5, stats, 40, 2, 6, "Unitas", 1,
                     info=info(week=week) if with_info else None, **fields)


def menu_rig(tmp_path, answers=(), preset=True, policy=None, **kwargs):
    """The program with the start-up choice ON. `preset`: a season of the Bengals in week 1 is in the files (True), or none."""
    rig = program_rig(tmp_path, answers, policy=policy, preset=preset_season() if preset is True else preset, **kwargs)
    rig.game.startup_menu = True
    return rig


def run_until_a_key_is_missing(rig):
    """Run until the program waits for a key the test does not press (the script is used up). The state at that moment is what was done
    without any key of the player."""
    try:
        rig.run()
    except AssertionError as exc:
        assert "never presses" in str(exc)
    return rig


def games(rig):
    """[(slot, score of the player's team)] of the saved games in the memory shelf."""
    return [(slot, entry.saved.stats[1].score) for slot, entry in sorted(rig.store.shelf.slots.items())]


def read_saved(store):
    """The first saved game a store's shelf holds (the old `take_saved_game` without the delete), or None."""
    entries = store.shelf.scan(store.classify)
    return entries[0].saved if entries and entries[0].saved is not None else None
