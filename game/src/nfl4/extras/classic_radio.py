"""Classic with the radio broadcast (nfl4 only, rule 0.13; BC.3, D-178, D-189). This is inspired by Jim Kitchen.

The owner (2026-10-26), asked whether Classic keeps the original's commentary: "Every mode": Classic keeps the original's plays and rules,
and with the comments on it uses the new radio broadcast (spec/NFL_BROADCAST_DESIGN.md section 1). The program's Classic is this object:
the engine's own ClassicRules (game/rules.CLASSIC, the original's answer to every hook, the golden transcript) with ONLY the broadcast added
at the hooks it already calls. The broadcast draws from its own generator and changes no state, so a Classic game makes exactly the draws of
the engine's Classic, comments on or off (tests/test_bc3_radio_crew.py proves it against the golden transcript's game).

    H1 period_clock        the original's play counter; the broadcast is attached to the game
    H2 before_snap         the drive is counted, the analyst on a fourth-down gamble      then "go on"
    H2 after_outcome       what the play was                                             the record unchanged
    H4 before_kickoff      a new possession; before the opening kick-off the sign-on     then "normal"
    H10 between_plays      the dead ball: the analyst, the announcer's asides             nothing
    H23 broadcast_moment   a touchdown, a score, the quarters, the breaks, the end       nothing more
"""
from __future__ import annotations

from ..game.rules import ClassicRules
from .broadcast import DEFAULT_TALK, Broadcast

KEY_F6 = "117"
HELP_F6 = ("NXH-65", "NXH-66", "NXH-83", "NXH-70")          # the broadcast's lines of F6 (the N. F. L. rules say them too)


class ClassicRadioRules(ClassicRules):
    name = "Classic"

    def __init__(self, broadcast_on: bool = True, crew_names: dict | None = None, crew_talk: str = ""):
        self.broadcast = Broadcast(self, analyst=broadcast_on, crew_names=crew_names, talk=crew_talk or DEFAULT_TALK)
        self.game = None
        self.state = None
        self.clock = None

    def for_game(self) -> "ClassicRadioRules":
        """A fresh object for one game, with the same switches and names (Game.play_game)."""
        return type(self)(self.broadcast.analyst, dict(self.broadcast.names), self.broadcast.talk_level)

    def period_clock(self, game, state):
        self.game, self.state = game, state
        self.clock = super().period_clock(game, state)
        self.broadcast.attach(game, state, self.clock)
        return self.clock

    def before_snap(self, state, offense_play: int, defense_play: int) -> str:
        self.broadcast.before_snap(state, offense_play)
        return super().before_snap(state, offense_play, defense_play)

    def after_outcome(self, state, outcome):
        self.broadcast.note_outcome(state, outcome)
        return super().after_outcome(state, outcome)

    def before_kickoff(self, state, kicking_side: int) -> str:
        self.broadcast.kickoff(state)
        return super().before_kickoff(state, kicking_side)

    def between_plays(self, state) -> None:
        self.broadcast.between(state)
        return super().between_plays(state)

    def broadcast_moment(self, state, what: str, quarter: int = 0) -> None:
        self.broadcast.moment(state, what, quarter)

    def extra_help(self, key: str) -> list[str]:
        """F6 names the radio crew after the classic help (the original's text stays word for word before it, rule 0.24)."""
        from . import nx_texts as X
        lines = super().extra_help(key)
        if key == KEY_F6:
            lines = list(lines) + [X.text(text_id) for text_id in HELP_F6]
        return lines


def classic_rules(game_settings) -> ClassicRadioRules:
    """The program's Classic for a Rules setting: the original's rules and the radio broadcast with the player's switch and names."""
    from . import crew
    return ClassicRadioRules(broadcast_on=getattr(game_settings, "nx_broadcast", True), crew_names=crew.names(game_settings),
                             crew_talk=getattr(game_settings, "nx_crew_talk", ""))
