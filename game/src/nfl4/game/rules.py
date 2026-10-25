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
    H3 menu_key(state, letter, item)       a letter that no item of the menu has (C when no challenge is allowed: it says why; D: the plain
                                           description of the current item, SX.10b2)  Classic: False, the key is the original's
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

Added in PX SX.2b (the T key, owner rule 0.22, D-084), never taken in Classic:
    H18 timeout_keys(state)                the T key calls a timeout in this game              False (the key is the original's)
    H18 timeout_key(state, live, undo, called)  T was pressed: kept for the end of a live play,     never called
                                           or refused with its sentence, or granted (the
                                           speech cut, the whistle, the sentences, the clock)
    H18 grant_kept_timeout(state)          a request kept during a live play is granted        nothing
                                           at the next dead-ball moment
    H18 withdraw_play(state)               a timeout granted before the snap: the plays that   nothing
                                           were called are withdrawn

Added in PX SX.10c (the catalog's offense in the game, D-093), each never taken in Classic:
    H3 menu_right(state, item)             the Right key in a play menu: a family's lists     False (the key is the original's)
    H3 menu_heading(state)                 what the menu says first instead of the coach's    "" (the coach and the prompt)
                                           prompt (the name of an open list)
    H3 menu_hint(state)                    SZ.5: one sentence after the first item of the     "" (nothing: the original's menus say no hint)
                                           catalog's top menu or its settings list, a few
                                           times only (where Right and M are, what the
                                           playbook's choice means)
    H3 menu_key(state, letter, item, code) a key no item has; `letter` is "" for a key that    False
                                           is not a letter; MENU_REFRESH: the items again,
                                           MENU_QUIET: nothing said (a lone Shift)
    H3 menu_action -> MENU_REFRESH         a setting changed: the items again, the same item  never called
    H19 model_play(state)                  after the snap sentence: the result of a catalog   None (the original's tables)
                                           play from the outcome models; the engine narrates
                                           it (game/pag_catalog.py)
    H19 turnover_return(state)             the turnover's spot: the catalog play's return      None (the original's random spot)
    H19 play_text(key, **values)           a sentence of the catalog's plays                   never called

Added in PX SX.10d (the defense calls and the kicks of 2026, D-094), each never taken in Classic:
    H4 before_kickoff -> KICKOFF_2026      the 2026 kick-off (the kick called is the extras':  never returned
                                           deep, short, squib, the safety punt); the engine's
                                           step kickoff_2026 tells it
    H20 special_kick(state, what)          the punt, the field goal or the extra point to come None (the original's kick)
                                           is a 2026 kick: its plan (the kind, a fake, the
                                           receivers' call, the distance)
    H20 kickoff_call / kickoff_result / kickoff_touchback / kick_result / fake_yards
                                           the kick-off called and the model's draws of a      never called
                                           2026 kick
    H20 kick_text(key, **values)           a sentence of the 2026 kicks                        never called
    H20 fair_catch(state, receivers, start)  a fair catch of a punt (the fair catch kick)      never called
    H10 between_plays -> FAIR_CATCH_KICK   the player chose the fair catch kick: the engine    never returned
                                           plays it as the next snap (a field goal, no rush)

Added in PX SX.10e (the computer's calling over the catalog, D-095), never taken in Classic:
    H21 computer_goes_for_two(state)       after the computer's touchdown: its two-point       False (the computer always
                                           chart (G26-10)                                     kicks, no draw)

Added in PX SX.12 (the 2026 overtime, Rule 16, D-096), each the original's answer in Classic:
    H22 overtime_follows(state)            a tied game at the end of a period that could end   True (sudden death until
                                           the game: another overtime period begins            a score)
    H24 sack_defenders(state)              the two defenders the sack sentence names                    (defender1, defender2): the draws
                                           (the player's blitzer, SY.5)
    H23 banter_lines(game)                 the announcer's banter draws its lines from these      None (the original's 142 lines
                                           (the radio banter of the N. F. L. rules, rule 0.27)    and the player's banter.txt)
    H23 broadcast_moment(state, what)      a moment of the broadcast: a touchdown (after its six points), a score (after the   nothing
                                           banter), the end of a quarter, the two-minute warning, half time, the end of the game
                                           (the crowd and Ghip, extras/stadium.py and broadcast.py)
    H22 overtime_lines(state)              said after " We are going into over time number "  no lines
    H22 overtime_toss(state)               the overtime begins with a coin toss                False (the side with the ball
                                                                                              at the end receives)
    H22 overtime_kicks_first(state)        the computer won the overtime toss: it kicks off    never called
    H22 points_end_game(state, td_by)      points were scored (a touchdown's six before its    quarter 5 and not a touchdown
                                           try: td_by its side): the game is decided now      before its try (every score
                                                                                              ends it after the try)
    H22 possession_ends_game(state)        after the possession sentence: the game is decided  False
    H22 period_end_step(state)             an overtime period ended: what the next one starts  None (the game's end decides)
                                           with (the play-offs: OT_SAME_BALL, OT_KICK_OFF,
                                           OT_COIN_TOSS)
    H22 overtime_fourth_down(state)        the computer's fourth down in overtime: "go",       None (the original's rule)
                                           "kick" (a field goal) or None
    H22 game_over_lines(state)             said after " THE GAME IS OVER" (the tie)            no lines
    H10 between_plays -> OVERTIME_OVER     the game was decided between two plays (the kickers  never returned
                                           kept their kick after their score, 16-1-5 (c))
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
KICKOFF_2026 = "2026 kick-off"  # H4: the kick-off of 2026 (N. F. L. rules mode with a playbook only, SX.10d)
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
# Save Game at the accept-or-decline prompt (N. F. L. rules mode only, SX.9, C10): the extras have put the board as if the penalty
# were declined and kept the choice in the extras record; the engine saves the game (save_game) and the loaded game asks it again
SAVE_PENDING = "save with the choice pending"
# The player chose the fair catch kick after a fair catch (N. F. L. rules mode with a playbook only, SX.10d): the engine plays it as its next
# snap, a field goal the extras tell as the fair catch kick
FAIR_CATCH_KICK = "fair catch kick"
# What the T key (H18, SX.2b) did: the request is kept for the end of the live play, a timeout was called, or it was refused (none left,
# one already called in this dead-ball period, the period over)
TIMEOUT_KEPT, TIMEOUT_GRANTED, TIMEOUT_REFUSED = "kept", "granted", "refused"
# What a play menu does after an added key or item (N. F. L. rules mode only, SX.10c): the items are made again and the menu stays at its
# place (a setting changed, a favourite was added or taken off), or nothing is said and the next key is waited for (a lone Shift)
MENU_REFRESH, MENU_QUIET = "menu refresh", "menu quiet"
# The 2026 overtime (N. F. L. rules mode only, SX.12): the game was decided between plays (H10), and what a play-off overtime period that ended
# without a winner starts the next one with (the same ball, down and distance; a kick-off; a coin toss and its kick-off)
OVERTIME_OVER = "overtime over"
OT_SAME_BALL, OT_KICK_OFF, OT_COIN_TOSS = "same ball", "kick off", "coin toss"


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

    def draw_defenders(self, state, rnd) -> tuple:
        """NX-D2's hook: the snap's two different defenders. The original: rnd(17), and rnd(17) again until it is another one."""
        first = rnd(17)
        second = rnd.redraw(lambda: rnd(17), lambda d: d != first, lambda: 2 if first == 1 else 1, "second defender")
        return first, second

    def start_sounds(self) -> bool:
        """The original's sounds at the start of a game (the crowd to full, foot0 waited): Classic plays them."""
        return True

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

    def menu_key(self, state, letter: str, item=None, code: str = ""):
        return False

    def menu_right(self, state, item) -> bool:
        return False

    def menu_heading(self, state) -> str:
        return ""

    def menu_hint(self, state) -> str:
        return ""

    # H19 (SX.10c): the catalog's plays. Classic plays the original's tables: no result, no draw, no word
    def model_play(self, state):
        return None

    def turnover_return(self, state):
        return None

    def play_text(self, key: str, **values) -> str:
        raise RuntimeError("Classic has no catalog plays: model_play never answers a result")

    # H20 (SX.10d): the kicks of 2026. Classic kicks as the original: no plan, no draw, no word
    def special_kick(self, state, what: str):
        return None

    # H21 (SX.10e): the computer's two-point chart. Classic: the computer always kicks (no draw)
    def computer_goes_for_two(self, state) -> bool:
        return False

    def kickoff_call(self, state) -> str:
        raise RuntimeError("Classic has no 2026 kick-off: before_kickoff never answers KICKOFF_2026")

    def kickoff_result(self, state):
        raise RuntimeError("Classic has no 2026 kick-off: before_kickoff never answers KICKOFF_2026")

    def kickoff_touchback(self) -> int:
        raise RuntimeError("Classic has no 2026 kick-off: before_kickoff never answers KICKOFF_2026")

    def kick_result(self, state, plan):
        raise RuntimeError("Classic has no 2026 kicks: special_kick never answers a plan")

    def fake_yards(self, state, plan) -> int:
        raise RuntimeError("Classic has no 2026 kicks: special_kick never answers a plan")

    def kick_text(self, key: str, **values) -> str:
        raise RuntimeError("Classic has no 2026 kicks")

    def fair_catch(self, state, receivers: int, start: int) -> None:
        raise RuntimeError("Classic has no 2026 kicks")

    def before_kickoff(self, state, kicking_side: int) -> str:
        return NORMAL_KICKOFF

    def onside_kick(self, state) -> str:
        raise RuntimeError("Classic has no onside kicks: before_kickoff never answers ONSIDE_KICKOFF")

    def between_plays(self, state) -> None:
        return None

    # H23 (SY.1, the radio broadcast, CLAUDE.md 0.27): Classic keeps the original's banter and has no commentator.
    def banter_lines(self, game):
        return None

    def sack_defenders(self, state) -> tuple[int, int]:
        """H24 (SY.5): the defenders a sack sentence names. Classic: the ones the snap drew."""
        return state.defender1, state.defender2

    def broadcast_moment(self, state, what: str, quarter: int = 0) -> None:
        return None

    def resume_choice(self, state) -> str | None:
        """A loaded game, or a Save Game that could not write the file: a choice the saved game kept is asked again (SX.9, C10).
        The engine's next step's answer, or None (Classic: always None, the play menu)."""
        return None

    # H18 (SX.2b, owner rule 0.22): the T key calls a timeout anywhere in a game until the play is run. Classic has no timeouts:
    # the key is the original's (an unknown key), the engine never asks for more than `timeout_keys`.
    def timeout_keys(self, state) -> bool:
        return False

    def timeout_key(self, state, live: bool, undo=None, called=None, where: str = "live play") -> str:
        raise RuntimeError("Classic has no timeouts: the T key is never handled")

    def grant_kept_timeout(self, state) -> None:
        return None

    def ball_live(self, state) -> None:
        return None

    def withdraw_play(self, state) -> None:
        return None

    # H22 (SX.12): the overtime. Classic answers every call with the original's sudden death (GAME_SPEC 5.6 item 6, 5.12): a tie at the
    # end of the fourth quarter or of an overtime period begins another period, received by the side that had the ball, and every score
    # ends the game (a touchdown after its try).
    def overtime_follows(self, state) -> bool:
        return True

    def overtime_lines(self, state) -> list[str]:
        return []

    def overtime_toss(self, state) -> bool:
        return False

    def overtime_kicks_first(self, state) -> bool:
        raise RuntimeError("Classic has no overtime toss: overtime_toss is always False")

    def overtime_toss_won(self, state, winner: int) -> None:
        raise RuntimeError("Classic has no overtime toss: overtime_toss is always False")

    def points_end_game(self, state, touchdown_by: int | None = None) -> bool:
        return state.quarter == 5 and touchdown_by is None

    def possession_ends_game(self, state) -> bool:
        return False

    def period_end_step(self, state) -> str | None:
        return None

    def overtime_fourth_down(self, state) -> str | None:
        return None

    def game_over_lines(self, state) -> list[str]:
        return []

    def extra_stats_lines(self, state) -> list[str]:
        return []

    def extra_situation(self, state) -> list[str]:
        return []

    def extra_help(self, key: str) -> list[str]:
        """F5 and F6 name every key of the game, the original's own and the game's added ones (CLAUDE.md 0.24: the master list
        game/key_list.py), and F7 adds the plain description of each of the original's plays after the original's football words
        (NX-P8): all after the original's text, which stays word for word. The original's keys themselves do not change."""
        from . import key_list
        lines = key_list.help_lines(key, "classic")
        if key == key_list.KEY_F7:
            from ..extras.plays import descriptions
            lines = descriptions.classic_f7_lines()
        return lines


CLASSIC = ClassicRules()
