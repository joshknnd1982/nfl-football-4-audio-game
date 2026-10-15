"""The period clock: every place of the game that reads the play counter reads it here (nfl4 hook H1). This is inspired by Jim Kitchen.

GAME_SPEC 5.3, 5.6 and 5.7 (CODE (lifted) pag): the original has no running clock. A period lasts L2cc(quarter) counted
plays; the counter L738 grows by one at every next-play step (0x43cd4d) and starts at 1 in quarters 1, 2 and 4 and at 0
in quarter 3 and every overtime period (Q14); the two-minute warning comes when the counter equals L2cc - M2W (quarter 2),
L2cc - M4W (quarter 4) or L2cc - M5W (overtime); F4 makes a time up from the counter (sgc). The computer's choices read
"plays of the period minus the counter" (5.7 items a and c) and "the counter" (quarter 4, "past 20").

NFL_EXTRAS_DESIGN 3 H1: these calls are the whole interface. ClassicPeriodClock answers every one of them from the counter
exactly as the original; the N. F. L. rules clock (SX.2) answers the same calls from seconds. `before_snap` (a pending
runoff) does nothing in Classic.
"""
from __future__ import annotations

from .gamestate import GameState

WARNING_QUARTERS = (2, 4, 5)


class ClassicPeriodClock:
    def __init__(self, game, state: GameState):
        self.game = game                      # Game: sgc and the warning lengths (quarter_clock)
        self.state = state

    def _total(self) -> int:
        return self.state.plays_in(self.state.quarter)

    def plays_left(self) -> int:
        """L2cc(L3c0) - L738."""
        return self._total() - self.state.counter

    def played(self) -> int:
        """L738."""
        return self.state.counter

    def is_last_play(self) -> bool:
        """`L2cc(L3c0) - L738 = 1` (0x43f1ad)."""
        return self.plays_left() == 1

    def period_over(self) -> bool:
        """`L738 >= L2cc(quarter)`."""
        return self.state.counter >= self._total()

    def _warning_point(self) -> int | None:
        quarter = self.state.quarter
        if quarter not in WARNING_QUARTERS and quarter < 5:
            return None
        return self._total() - self.game.quarter_clock.warning[min(quarter, 5)]

    def warning_zone(self) -> bool:
        """`L738 >= L2cc - W` (quarters 2, 4 and overtime): the original turns the log flag on and off there."""
        point = self._warning_point()
        return point is not None and self.state.counter >= point

    def warning_due(self) -> bool:
        """`L738 = L2cc - M2W` (quarter 2), `- M4W` (quarter 4), `- M5W` (overtime); never in quarters 1 and 3."""
        point = self._warning_point()
        return point is not None and self.state.counter == point

    def speak(self) -> None:
        """F4: sgc(L738, L2cc(L3c0), L3c0)."""
        self.game.sgc(self.state.counter, self._total(), self.state.quarter)

    def after_play(self, outcome=None) -> None:
        """The next-play step: L738 = L738 + 1."""
        self.state.counter += 1

    def start_period(self, counter: int) -> None:
        """L738 = 1 (quarters 2 and 4) or 0 (quarter 3, overtime)."""
        self.state.counter = counter

    def before_snap(self) -> None:
        """A pending runoff (N. F. L. rules mode); nothing in Classic."""
