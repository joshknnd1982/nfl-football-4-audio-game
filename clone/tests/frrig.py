"""A rig for the Franchise (nfl4 only, rule 0.13): the whole program on the virtual clock with the N. F. L. rules, a franchise in
memory, a stand-in for pag whose scores the test scripts, and the REAL season engine (pog and finplay17), so the hooks of H14
fire as they do in play. This is inspired by Jim Kitchen.

* `franchise_rig` builds the rig of tests/programrig.py, sets the Rules to the N. F. L. rules (and the kind of season when asked),
  puts a `FranchiseStore` over `MemoryFiles` into the Game (`rig.files`, `rig.fstore`; strict: a record that fails its own check
  raises) and replaces the stand-in's pog by the engine's. Pass `files=` to start a second program over the same folder (a
  restart).
* The stand-in game returns `rig.scores(rig)` (own, opponent): by default the player wins when the week is odd. A game of the
  Super Bowl week plays the Super Bowl presentation and leaves gtp 0, as pag does.
* `WANT_FRANCHISE` is the answer script of the new-season question for "franchise": Down, Enter; `COACH_AND_TEAM` is the
  original's GetCoach and ChooseTeam.
"""
import random

from programrig import DOWN, ENTER, F1, F5, F9, ESC, UP, program_rig, said, enter_policy  # noqa: F401 (re-exported)

from nfl4.extras.franchise.files import MemoryFiles
from nfl4.extras.franchise.store import FranchiseStore
from nfl4.game.pag import GameResult

COACH_AND_TEAM = ["k", "i", "m", ENTER, ENTER, ENTER, ENTER]          # kim, yes; the first team (the Bengals), yes
WANT_FRANCHISE = [DOWN, ENTER]
WANT_CLASSIC = [ENTER]


def odd_week_wins(rig):
    """The player wins in odd weeks; in the play-offs he wins the wild card and the division games, loses the rest."""
    gtp = rig.game.season.gtp
    if gtp <= 16:
        return (24, 17) if gtp % 2 else (10, 31)
    return (24, 17) if gtp in (17, 18) else (10, 31)


def franchise_rig(tmp_path, answers=(), policy=enter_policy, files=None, kind=None, scores=odd_week_wins, seed=1, nfl=True,
                  preset=None, classic_names=None, **kwargs):
    rig = program_rig(tmp_path, answers, policy, fast=True, seed=seed, preset=preset, pog=None, **kwargs)
    game = rig.game
    settings = game.options.settings.game
    if nfl:
        settings.rules = "nfl"
        game.apply_rules_setting()
    if kind is not None:
        settings.nx_season_kind = kind
    rig.files = files if files is not None else MemoryFiles()
    rig.scores = scores
    rig.classic_names = classic_names
    if classic_names is not None:
        rig.store.names = classic_names

    def factory(classic):
        store = FranchiseStore(rig.files, classic)
        store.strict = True
        rig.fstore = store
        return store

    rig.fstore = None
    game.franchise_factory = factory
    game.pog = lambda: (rig.pog_calls.append(game.m414), game.season_engine.pog())[1]

    def play_game(rules=None, own_names=None, saved=None, quarterback_names=None, save_sink=None, roster_sink=None,
                  opponent_names=None, **ignored):
        rig.plays.append({"own_names": own_names, "saved": saved, "save_sink": save_sink, "roster_sink": roster_sink,
                          "gtp": game.season.gtp, "opponent": (game.season.tn3, game.season.tn4),
                          "opponent_names": opponent_names, "quarterback_names": quarterback_names})
        outcome = rig.outcomes.pop(0) if rig.outcomes else None
        if callable(outcome):
            outcome = outcome(rig)
        if outcome is not None:
            result = outcome.result
            if outcome.gtp is not None:
                game.season.gtp = outcome.gtp
            if outcome.stop_beds:
                rig.sounds.stop_crowds()
            if result.scores is not None:
                game.m414 = result.scores
            return result
        own, opponent = rig.scores(rig)
        game.m414 = (own, opponent)
        if game.season.gtp == 20:                         # the Super Bowl game: the presentation, then the season is over
            game.superbowl((own, opponent))
            game.season.gtp = 0
        rig.sounds.stop_crowds()
        return GameResult(scores=(own, opponent))

    game.play_game = play_game
    return rig


def enter_until(predicate, limit=20000):
    """A policy: Enter at every wait until `predicate()` is true, then the window closes (GameQuit). The predicate is asked only
    at a wait for a key; a state that never shows at a wait would run for ever, so after `limit` waits the test fails (B-T46)."""
    from nfl4.game.keys import GameQuit
    asked = [0]

    def policy(keys):
        if predicate():
            raise GameQuit()
        asked[0] += 1
        if asked[0] > limit:
            raise AssertionError("the state the test waits for did not show at any of %d waits" % limit)
        return ENTER
    return policy


def quit_policy(keys):
    """The window closes as soon as the scripted keys are used up."""
    from nfl4.game.keys import GameQuit
    raise GameQuit()


def run_until(rig):
    """Run the program until its policy closes the window."""
    from nfl4.game.keys import GameQuit
    try:
        rig.run()
    except GameQuit:
        pass
    return rig


def spoken(rig):
    return said(rig)


def league_of(rig):
    return rig.fstore.league if rig.fstore is not None else None


def play_weeks(count):
    """The key script for `count` weeks of "play game": the menu's Enter. The standings, the results and every other wait
    take the policy's Enter."""
    return [ENTER] * count


__all__ = ["franchise_rig", "enter_until", "quit_policy", "run_until", "COACH_AND_TEAM", "WANT_FRANCHISE", "WANT_CLASSIC", "odd_week_wins", "spoken", "league_of",
           "play_weeks", "ENTER", "DOWN", "UP", "F1", "F5", "F9", "ESC", "random"]
