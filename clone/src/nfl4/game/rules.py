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

Added in PX SX.4 (onside kicks, D-051), each never taken in Classic:
    H4 before_kickoff -> ONSIDE_KICKOFF    the kick-off is an onside kick (the question or     never returned
                                           the computer's declaration came first)
    H4 onside_kick(state)                  the kick's sentences, sounds and draws up to its    never called
                                           result: ONSIDE_KEPT, ONSIDE_LOST or ONSIDE_RUN
    H4 safety_kick / kick again            kept by the extras' own record (no hook)

Added in PX SX.5 (quarterback runs, D-052), each never taken in Classic:
    H3 offense_menu                        items 8, 9 and 0: Quarterback Sneak, Keeper and Draw (offense play 8, 9, 10)
    H8 qb_entry(state)                     the outcome row of a quarterback run (QBRunEntry) against the defense call
    H8 qb_narrate(state, entry, d1, d2)    the start sentence of the pool QB, the direction, the run and tackle sentences
    H8 qb_slide(state)                     the slide after a gain of 8 or more yards (yards, tackle sentence, whistle)
    H2 instead_of_sack -> SCRAMBLE         the original's draw gave a sack: the quarterback takes off running
    H2 instead_of_incompletion(state)      the original's draw gave an incompletion (before the throw sentence): a scramble
    H2 computer_offense(state)             the computer's offense may replace its drawn play by a sneak, keeper or draw

Added in PX SX.6 (replay challenges, booth reviews and the ruling model, D-053), each never taken in Classic:
    H2 after_outcome -> outcome.then       a booth review reversed the ruling on the field: the board is as it was at the end
                                           point with the corrected result set (REVIEWED_FIELD, REVIEWED_TOUCHDOWN,
                                           REVIEWED_FUMBLE: the engine's steps gain_and_end, touchdown_reached, reviewed_fumble)
    H3 menu_action -> a continuation       the player's challenge reversed a ruling: the menu is left for the step it names
    H3 menu_key(state, letter)             a letter that no item of the menu has (C when no challenge is allowed): it says why
    H10 between_plays -> a continuation    the computer's challenge reversed a ruling: the engine goes on at the step it names

Added in PX SX.7 (playbooks, D-054), each never taken in Classic:
    H3 menu_action -> (PLAY, n)            a play of a playbook was chosen: the menu returns it as a chosen play (a group item opens
                                           its plays and a Back item closes them: True, the menu starts again)
    H3 menu_back(state)                    Backspace or Left: out of a group of plays (Classic: False, the key is the original's)
    H2 computer_defense(state)             the computer's defense family is chosen: the style's play of it
    H8 modifiers                           PlaybookModifiers: the rows move by the two plays called (never in Classic: NEUTRAL)

Added in PX SX.8k (injuries, FRANCHISE ONLY, D-071), never taken in Classic and never outside a franchise game:
    H16 after_draws(state)                 at the end of the snap's draws (carrier, two     nothing (no draw, no word)
                                           defenders): a Franchise game whose next man up
                                           plays two places keeps the two tacklers two men
    H16 second_tackler(state, first, second)  the kick-off return's two tacklers, the same     the second unchanged
    H2 after_outcome                       the draws of a play that can hurt a player and the announcer's line (NflRules, only when the
                                           game has the Franchise's injuries: Game.game_injuries)

Added in PX SX.8o (the game's later items, D-075), never taken in Classic and never outside a franchise game:
    H17 draw_carrier(state, rnd)           the snap's draw of the ball carrier (snap_draws)   rnd(6), the original's draw
    H8 return_shortest(side, returner)     the kick-off return's shortest length              RETURN_SHORTEST (12)
"""
from __future__ import annotations

from . import menus
from .outcome import PlayOutcome
from .periodclock import ClassicPeriodClock
from .playtables import NEUTRAL, Modifiers

GO_ON = "go on"
NORMAL_KICKOFF = "normal"
ONSIDE_KICKOFF = "onside"       # H4: the kick-off is an onside kick (N. F. L. rules mode only, SX.4)
PERIOD_OVER = "period over"     # H4: no kick-off, the period ends first (N. F. L. rules mode only, SX.2)
# What the extras' onside kick leaves for the engine (SX.4): the kicking team recovered it, the receivers fell on it, or the
# receivers picked it up and the engine runs the return (the state is set like a kick-off return)
ONSIDE_KEPT, ONSIDE_LOST, ONSIDE_RUN = "kept", "lost", "run"
SCRAMBLE = "scramble"           # H2 instead_of_sack: the sack becomes a scramble (N. F. L. rules mode only, SX.5)
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
# What the engine does after a review changed the ruling of a play (N. F. L. rules mode only, SX.6). The extras have set the
# board as it was at the narration end point of the play and the corrected result in the state (the yards, the kind).
REVIEWED_FIELD = "reviewed field play"      # the gain sentence of the corrected yards, the end point, the downs (gain_and_end)
REVIEWED_TOUCHDOWN = "reviewed touchdown"   # the score the ruling had denied: the touchdown step after its countdown
REVIEWED_FUMBLE = "reviewed fumble"         # the fumble the ruling had called down: the ball turns over (reviewed_fumble)


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

    def after_draws(self, state) -> None:
        return None

    def draw_carrier(self, state, rnd) -> int:
        return rnd(6)

    def second_tackler(self, state, first: int, second: int) -> int:
        return second

    def instead_of_incompletion(self, state) -> bool:
        return False

    def computer_offense(self, state) -> None:
        return None

    def computer_defense(self, state) -> None:
        return None

    def menu_back(self, state) -> bool:
        return False

    def qb_entry(self, state, scramble: bool = False):
        raise RuntimeError("Classic has no quarterback runs: the menu never offers plays 8 to 10")

    def qb_narrate(self, state, entry, defender1: str, defender2: str):
        raise RuntimeError("Classic has no quarterback runs")

    def qb_slide(self, state) -> None:
        raise RuntimeError("Classic has no quarterback runs")

    def after_tackle(self, state) -> None:
        return None

    def after_outcome(self, state, outcome: PlayOutcome) -> PlayOutcome:
        return outcome

    def offense_menu(self, state, two_point_try: bool) -> list[menus.MenuItem]:
        return menus.offense_menu(two_point_try)

    def defense_menu(self, state) -> list[menus.MenuItem]:
        return menus.defense_menu()

    def menu_action(self, state, action: tuple[str, int]):
        return False

    def menu_key(self, state, letter: str) -> bool:
        return False

    def before_kickoff(self, state, kicking_side: int) -> str:
        return NORMAL_KICKOFF

    def onside_kick(self, state) -> str:
        raise RuntimeError("Classic has no onside kicks: before_kickoff never answers ONSIDE_KICKOFF")

    def between_plays(self, state) -> None:
        return None

    def extra_stats_lines(self, state) -> list[str]:
        return []

    def extra_situation(self, state) -> list[str]:
        return []

    def extra_help(self, key: str) -> list[str]:
        return []


CLASSIC = ClassicRules()
