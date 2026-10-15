"""The extras' record of one game: GameState.extras in N. F. L. rules mode (nfl4 only, rule 0.13; hook H5). This is inspired by Jim Kitchen.

NFL_EXTRAS_DESIGN 3 H5 and 12.3. Plain data and nothing else (no reference to the game, the rules or the speech), so
GameState.snapshot can copy it and Save Game can write it as one UTF-8 JSON string after the original's values and D-027's
Variant (data/files/savedgame.py). Sides are 1 (the player) and 2 (the computer); per-side values are lists of two, side 1
first, so the JSON stays plain.

`from_json` refuses anything it cannot use whole (a damaged string): the caller then starts the extras from their start
values with one spoken notice (C10, playbook 7.10) while the original's values still load.
"""
from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field, fields

from . import rules_2026 as R
from . import tuning as T

log = logging.getLogger("nfl4.extras")

FORMAT = 1                     # the Integer written after the marker in football.sav
MARKER = "NX-EXTRAS"           # the string that starts the extras section of football.sav
RECENT_REMARKS = 3             # a remark is never one of the last three spoken of its pool
MAX_TIMEOUTS = max(R.TIMEOUTS_PER_HALF, R.OT_REGULAR_TIMEOUTS, R.OT_POST_TIMEOUTS)


@dataclass
class ExtrasRecord:
    rules_year: int = R.YEAR
    timeouts_on: bool = True          # the Time outs switch of the game (design 12.1)
    postseason: bool = False          # a play-off game: the overtime periods last 15 minutes and share timeouts in pairs
    # the clock (design 5)
    period: int = 1                   # 1 to 4, then 5, 6, ... for the overtime periods (4 + the overtime number)
    left: int = R.QUARTER_SECONDS     # whole seconds left in the period at the end of the last play
    pending: int = 0                  # the runoff kept until the next snap (design 5.3); 0 when the clock is stopped
    running: bool = False             # the clock runs from now to the next snap
    warning_due: bool = False         # the two-minute warning is to be given before the next play
    warning_given: bool = False       # in this period
    # the last play, for H10 (the runoff is drawn once per play: `handled` is the play it was drawn for)
    plays: int = 0                    # plays ended in this game (every narration end point, H2)
    handled: int = 0
    last_kind: str = ""
    last_offense: int = 0
    last_two_point: bool = False
    out_of_bounds: bool = False       # the runner or receiver of the play just ended went out of bounds (design 5.2)
    # timeouts (design 6.3)
    unit: str = "H1"                  # H1, H2, OT<n> (regular season, every period) or OTP<k> (play-offs, a pair)
    announced: str = ""               # the unit whose timeouts were announced at its first kick-off
    timeouts: list = field(default_factory=lambda: [R.TIMEOUTS_PER_HALF, R.TIMEOUTS_PER_HALF])
    used: list = field(default_factory=lambda: [0, 0])          # charged timeouts of the whole game (the statistics)
    called: list = field(default_factory=lambda: [False, False])  # a timeout in this dead-ball period (4-5-1 Item 3)
    # the remarks of the extras: the IDs spoken last, per pool (CUSTOMIZABLE_CONTENT 13)
    recent: dict = field(default_factory=dict)

    # ----- per side -----

    def timeouts_of(self, side: int) -> int:
        return self.timeouts[side - 1]

    def used_of(self, side: int) -> int:
        return self.used[side - 1]

    def called_by(self, side: int) -> bool:
        return self.called[side - 1]

    # ----- the save -----

    def load_saved(self, saved) -> bool:
        """GameState.load (H5) with the N. F. L. rules: the save's own record (its mode and state, C1), or the start values
        for this saved game (design 12.3: full timeouts, the clock at the period's length minus 28 seconds per counted play,
        at least 1:00; no announcement and no warning already passed). Returns True when the save's record was used."""
        if saved.extras is not None:
            try:
                loaded = ExtrasRecord.from_json(saved.extras)
            except ValueError as exc:
                log.warning("the saved extras cannot be used (%s): the extras start from their start values", exc)
            else:
                for f in fields(self):
                    setattr(self, f.name, getattr(loaded, f.name))
                return True
        from .clock import is_warning_period, period_seconds
        from .timeouts import count_for, unit_for
        self.period = saved.quarter if saved.quarter <= 4 else 5
        length = period_seconds(self.period, self.postseason)
        self.left = min(length, max(T.SAVE_LEAST_LEFT, length - T.SAVE_SECONDS_PER_COUNTED_PLAY * saved.counter))
        self.pending, self.running = 0, False
        self.warning_due = False
        self.warning_given = is_warning_period(self.period, self.postseason) and self.left <= R.WARNING_SECONDS
        self.out_of_bounds = False
        self.unit = self.announced = unit_for(self.period, self.postseason)
        count = count_for(self.unit)
        self.timeouts, self.used, self.called = [count, count], [0, 0], [False, False]
        self.plays = self.handled = 0
        return False

    def to_json(self) -> str:
        return json.dumps(asdict(self), sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_json(cls, text: str) -> "ExtrasRecord":
        """The record a save holds. ValueError when the string is not a whole, sensible record."""
        try:
            data = json.loads(text)
        except (ValueError, TypeError, RecursionError) as exc:      # RecursionError: brackets nested thousands deep
            raise ValueError("the extras are not JSON: %s" % exc) from exc
        if not isinstance(data, dict):
            raise ValueError("the extras are not a record")
        record = cls()
        names = {f.name for f in fields(cls)}
        for name, value in data.items():
            if name in names:
                setattr(record, name, value)
        record.check()
        return record

    def check(self) -> None:
        """Every value in its range (a save edited by hand or cut short is refused, never half used)."""
        def whole(value, low, high, what):
            if isinstance(value, bool) or not isinstance(value, int) or not low <= value <= high:
                raise ValueError("%s is %r" % (what, value))

        def flag(value, what):
            if not isinstance(value, bool):
                raise ValueError("%s is %r" % (what, value))

        def pair(values, check, what):
            if not isinstance(values, list) or len(values) != 2:
                raise ValueError("%s is %r" % (what, values))
            for value in values:
                check(value, what)

        whole(self.rules_year, R.YEAR, R.YEAR, "the rules year")
        whole(self.period, 1, 999, "the period")
        whole(self.left, 0, R.QUARTER_SECONDS, "the time left")
        whole(self.pending, 0, 3600, "the pending runoff")
        whole(self.plays, 0, 100000, "the plays")
        whole(self.handled, 0, 100000, "the handled play")
        whole(self.last_offense, 0, 2, "the last offense")
        for name in ("timeouts_on", "postseason", "running", "warning_due", "warning_given", "last_two_point",
                     "out_of_bounds"):
            flag(getattr(self, name), name)
        for name in ("last_kind", "unit", "announced"):
            if not isinstance(getattr(self, name), str) or len(getattr(self, name)) > 40:
                raise ValueError("%s is %r" % (name, getattr(self, name)))
        pair(self.timeouts, lambda v, w: whole(v, 0, MAX_TIMEOUTS, w), "the timeouts")
        pair(self.used, lambda v, w: whole(v, 0, 999, w), "the timeouts used")
        pair(self.called, flag, "the timeouts called")
        if not isinstance(self.recent, dict) or len(self.recent) > 20:
            raise ValueError("the recent remarks are %r" % (self.recent,))
        for pool, ids in self.recent.items():
            if not isinstance(pool, str) or not isinstance(ids, list) or len(ids) > RECENT_REMARKS:
                raise ValueError("the recent remarks of %r are %r" % (pool, ids))
            if any(not isinstance(i, str) or len(i) > 12 for i in ids):
                raise ValueError("a recent remark ID of %r is not an ID" % (pool,))
