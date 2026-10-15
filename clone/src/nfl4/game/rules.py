"""The Rules object the play engine is given (nfl4 hooks H6, H2, H3, H4, H8, H10, H11, H13). This is inspired by Jim Kitchen.

NFL_EXTRAS_DESIGN 3 and NFL_EXTRA_FEATURES 5 (nfl4 only, CLAUDE.md rule 0.13): the classic engine is exact, and the seven
extra features of the N. F. L. rules mode (built in phase PX, in the package `extras`) reach it only through these calls. The engine
never tests a feature flag in the middle of GAME_SPEC 5.7 to 5.12; it calls the hook, and ClassicRules answers every call
with the original's behavior: an identity or nothing, and never a random number (C4) and never a spoken word (P1).

    hook                                   where the engine calls it                      Classic
    H1 period_clock(game, state)           built once per game                            the play counter (periodclock.py)
    H2 before_snap(state, play, defense)   after the choice, before the snap (0x43fd12)   "go on"
    H2 after_outcome(state, outcome)       at the narration end point of every play       the record unchanged
    H3 offense_menu / defense_menu         every play menu                                the lists of 4.15
    H4 before_kickoff(state, kicking)      before every kick-off (0x444645)               "normal"
    H8 modifiers                           every read of the outcome tables               NEUTRAL
    H10 between_plays(state)               after the down sentence, before the next menu  nothing
    H11 extra_stats_lines(state)           after " Points Scored" in the statistics        no lines
    H13 extra_situation(state)             after F1's position and down in a play menu     no lines
H12 (added help on F5, F6 and F7) comes with the hot-key menus in S7.4.
"""
from __future__ import annotations

from . import menus
from .outcome import PlayOutcome
from .periodclock import ClassicPeriodClock
from .playtables import NEUTRAL, Modifiers

GO_ON = "go on"
NORMAL_KICKOFF = "normal"


class ClassicRules:
    name = "Classic"
    modifiers: Modifiers = NEUTRAL

    def period_clock(self, game, state) -> ClassicPeriodClock:
        return ClassicPeriodClock(game, state)

    def before_snap(self, state, offense_play: int, defense_play: int) -> str:
        return GO_ON

    def after_outcome(self, state, outcome: PlayOutcome) -> PlayOutcome:
        return outcome

    def offense_menu(self, state, two_point_try: bool) -> list[menus.MenuItem]:
        return menus.offense_menu(two_point_try)

    def defense_menu(self, state) -> list[menus.MenuItem]:
        return menus.defense_menu()

    def before_kickoff(self, state, kicking_side: int) -> str:
        return NORMAL_KICKOFF

    def between_plays(self, state) -> None:
        return None

    def extra_stats_lines(self, state) -> list[str]:
        return []

    def extra_situation(self, state) -> list[str]:
        return []


CLASSIC = ClassicRules()
