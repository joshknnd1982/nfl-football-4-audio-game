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
    H12 extra_help(key)                    F5, F6, F7 after the original text (S7.4a)     no lines
H12 is read by the hot-key menus (game/hotkeys.py) through the rules of the game in progress, else Game.rules, the rules
of the whole program; key is the code text of the key ("116" F5, "117" F6, "118" F7).

Added in PX SX.2 (the real clock and the timeouts, D-049), each an identity or a no-op in Classic:
    H2 after_tackle(state)                 after the tackle sentence of a play that ends     nothing
                                           in the field of play (0x4506ef)
    H3 menu_action(state, action)          Enter on an item whose action is neither a play   never called (the lists
                                           nor Save Game (an item the extras added)           of 4.15 have none)
    H4 before_kickoff -> PERIOD_OVER       a score as time ran out ends the period first      never returned
    H1 before_snap() -> True               a pending runoff ran the period out at the snap   None
    H1 warning_given()                     the engine said the two-minute warning            nothing
    for_game()                             the rules object of one game                       itself

Added in PX SX.3 (penalties with accept or decline, D-050), each never taken in Classic:
    H2 before_snap -> FOUL_BEFORE_SNAP     a dead-ball foul before the snap: the snap count   never returned
                                           stops after " hut 1 ", foul_before_snap(state)
                                           says it and returns what the engine does next
    H2 after_outcome: outcome.then         the extras took over the end of the play (an        None
                                           accepted penalty): the engine goes on with the
                                           step `then` names instead of the original's
    H2 instead_of_sack(state)              the original's draw gave a sack: the passer may     None
                                           throw the ball away (intentional grounding); the
                                           sentence that replaces the sack, or None
"""
from __future__ import annotations

from . import menus
from .outcome import PlayOutcome
from .periodclock import ClassicPeriodClock
from .playtables import NEUTRAL, Modifiers

GO_ON = "go on"
NORMAL_KICKOFF = "normal"
PERIOD_OVER = "period over"     # H4: no kick-off, the period ends first (N. F. L. rules mode only, SX.2)
FOUL_BEFORE_SNAP = "foul before the snap"   # H2 step 2 (SX.3): a dead-ball foul, the play is not run

# What the engine does after the extras took over a play (H2 step 4, `PlayOutcome.then`, or foul_before_snap's answer;
# N. F. L. rules mode only, SX.3). The extras have set the ball, the down and the distance in the state.
NEXT_DOWN = "next down"         # the position and down sentences (5.11 item 5), then the next play
ON_DOWNS = "on downs"           # the ball turned over on downs at the spot the extras set (the possession sentence)
SAFETY_BY_PENALTY = "safety"    # " in the end zone for a safety", 2 points to the defense, the free kick
TRY_AGAIN = "try again"         # the two-point try is played again from the spot the extras set
TRY_FAILS = "try fails"         # the two-point try fails (no points)
KICK_AGAIN = "kick again"       # the kick-off is made again
PERIOD_END = "period end"       # the period ends (a run off took its last seconds) without counting a play


class ClassicRules:
    name = "Classic"
    modifiers: Modifiers = NEUTRAL

    def for_game(self) -> "ClassicRules":
        return self

    def period_clock(self, game, state) -> ClassicPeriodClock:
        return ClassicPeriodClock(game, state)

    def before_snap(self, state, offense_play: int, defense_play: int) -> str:
        return GO_ON

    def foul_before_snap(self, state) -> str:
        raise RuntimeError("Classic has no penalties: before_snap never answers FOUL_BEFORE_SNAP")

    def instead_of_sack(self, state) -> str | None:
        return None

    def after_tackle(self, state) -> None:
        return None

    def after_outcome(self, state, outcome: PlayOutcome) -> PlayOutcome:
        return outcome

    def offense_menu(self, state, two_point_try: bool) -> list[menus.MenuItem]:
        return menus.offense_menu(two_point_try)

    def defense_menu(self, state) -> list[menus.MenuItem]:
        return menus.defense_menu()

    def menu_action(self, state, action: tuple[str, int]) -> bool:
        return False

    def before_kickoff(self, state, kicking_side: int) -> str:
        return NORMAL_KICKOFF

    def between_plays(self, state) -> None:
        return None

    def extra_stats_lines(self, state) -> list[str]:
        return []

    def extra_situation(self, state) -> list[str]:
        return []

    def extra_help(self, key: str) -> list[str]:
        return []


CLASSIC = ClassicRules()
