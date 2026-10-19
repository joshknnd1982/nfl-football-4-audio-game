"""The outcome tables of the play engine as data (GAME_SPEC 5.9 and 5.10; nfl4 hook H8). This is inspired by Jim Kitchen.

CODE (lifted) pag p_43a860: the 30 entries the pair (offense play 1 to 5, defense play 1 to 6) selects through the two
`On ... GoTo` tables (0x4614b6, 0x4614ca; checked against the asm by work/dump_jumptables_s34.py), with the original's
own variables: yards = Int(Rnd * (L548 - L44)) + L44, so `low` is L44 and `high` is L548, one more than the most yards;
`sound` is L4f0, the PlayTackle number of a run (1 = foot4, 2 = foot5, 3 = foot6); `sack` and `complete` are the
percentages L360 and L78c of a pass. The kicks' numbers are here too. Every number was read from its lifted line (the
address is next to it) and is compared with GAME_SPEC 5.9 by tests/test_playtables.py.

NFL_EXTRAS_DESIGN 3 H8: the engine reads these tables only through one `Modifiers` object. Classic passes NEUTRAL, which
returns every entry unchanged, so the numbers below are what Classic plays (C3: neutral equals classic). Playbooks,
ratings and the quarterback runs (SX.5, SX.7, SX.8) bring their own Modifiers; nothing here changes for them.
"""
from __future__ import annotations

from typing import NamedTuple

LINE_PLUNGE, END_RUN, SCREEN_PASS, SHORT_PASS, LONG_PASS, FIELD_GOAL, PUNT = 1, 2, 3, 4, 5, 6, 7
GOAL_LINE, SHORT_RUN, LONG_RUN, BLITZ, SHORT_PASS_D, LONG_PASS_D = 1, 2, 3, 4, 5, 6


class RunEntry(NamedTuple):
    """One run of the 5.9 table. direction: None, 3 (Int(Rnd * 3) + 1, Me.m3f8 1 to 3) or 4 (Int(Rnd * 4) + 4,
    Me.m3f8 4 to 7), drawn right after the hand-off sentence."""
    key: str            # which sentence pair (the engine builds the texts from it, game/pag_scrimmage.py)
    direction: int | None
    sound: int          # L4f0
    low: int            # L44
    high: int           # L548: yards = Int(Rnd * (high - low)) + low


class QBRunEntry(NamedTuple):
    """One quarterback run of the N. F. L. rules mode (SX.5, nfl4 only; design 7.1): a sneak, keeper, draw or scramble against
    one defense call. Classic never reads one. Yards = Int(Rnd * (high - low)) + low, so `high` is one more than the most
    yards; the fumble chance is 1 in `fumble`."""
    key: str            # "sneak", "keeper", "draw" or "scramble"
    direction: int | None    # 4: Int(Rnd * 4) + 4 as the original's End Run (the keeper's run sentence), else None
    sound: int          # the PlayTackle number of the tackle
    low: int
    high: int
    fumble: int


class PassEntry(NamedTuple):
    low: int            # L44
    high: int           # L548
    sack: int           # L360: a sack when Rnd * 100 (a Single) <= sack
    complete: int       # L78c: complete when Rnd * 100 < complete, and the interception rule's start


RUNS: dict[tuple[int, int], RunEntry] = {
    (1, 1): RunEntry("plunge_goal_line", None, 1, -3, 2),       # 0x446e29
    (1, 2): RunEntry("plunge_short_run", None, 3, -1, 5),       # 0x446fb7
    (1, 3): RunEntry("plunge_long_run", 3, 3, 0, 7),            # 0x447234
    (1, 4): RunEntry("plunge_blitz", None, 3, -5, 11),          # 0x447561
    (1, 5): RunEntry("plunge_short_pass", 3, 2, 8, 15),         # 0x447858
    (1, 6): RunEntry("plunge_long_pass", 3, 2, 11, 30),         # 0x447c72
    (2, 1): RunEntry("end_goal_line", 4, 3, -3, 3),             # 0x44808c
    (2, 2): RunEntry("end_short_run", 4, 3, -5, 0),             # 0x4483cb (no run sentence)
    (2, 3): RunEntry("end_long_run", 4, 3, -7, 0),              # 0x4486b5
    (2, 4): RunEntry("end_blitz", 4, 3, -7, 10),                # 0x4489cf
    (2, 5): RunEntry("end_short_pass", 4, 3, 3, 13),            # 0x448dd6
    (2, 6): RunEntry("end_long_pass", 4, 2, 11, 30),            # 0x449129
}

PASSES: dict[tuple[int, int], PassEntry] = {
    (3, 1): PassEntry(-3, 10, 5, 90), (3, 2): PassEntry(-3, 10, 5, 90), (3, 3): PassEntry(1, 15, 5, 90),
    (3, 4): PassEntry(11, 100, 50, 90), (3, 5): PassEntry(-7, 5, 5, 90), (3, 6): PassEntry(3, 15, 5, 90),       # 0x449558..
    (4, 1): PassEntry(1, 10, 10, 70), (4, 2): PassEntry(1, 10, 10, 70), (4, 3): PassEntry(5, 15, 10, 70),
    (4, 4): PassEntry(5, 50, 50, 70), (4, 5): PassEntry(1, 10, 25, 70), (4, 6): PassEntry(5, 15, 25, 70),        # 0x449978..
    (5, 1): PassEntry(15, 50, 10, 40), (5, 2): PassEntry(15, 50, 15, 40), (5, 3): PassEntry(15, 50, 10, 40),
    (5, 4): PassEntry(15, 100, 60, 40), (5, 5): PassEntry(15, 30, 20, 40), (5, 6): PassEntry(15, 50, 25, 30),    # 0x449d98..
}

# The computer's defense when it matches a repeated play (5.7): the original's five plays (1 to 5), and the quarterback runs
# of the N. F. L. rules mode (8 sneak, 9 keeper, 10 draw; design 7.4): Goal Line, Long Run, Short Run
DEFENSE_MATCH = {1: 1, 2: 3, 3: 5, 4: 5, 5: 6, 8: 1, 9: 3, 10: 2}
QB_SNEAK, QB_KEEPER, QB_DRAW = 8, 9, 10      # the offense play numbers of the quarterback runs (menu items 8, 9 and 0)

SACK = PassEntry(-12, 0, 0, 0)          # a sack's yards: Int(Rnd * 12) - 12 = -12 to -1 (0x44b294); sound 3, "smother" 2
SACK_PHRASES, THROW_COUNT, CATCH_COUNT, INCOMPLETE_COUNT = 6, 9, 9, 9
FUMBLE_ODDS, FUMBLE_NUMBER = 50, 13     # Int(Rnd * 50) + 1 = 13 is a fumble (0x44d97a)
INTERCEPTION_STEP = 3                   # L8c grows by 3 with every pass (0x44a293); the chance is 1 / max(2, C - L8c)
INTERCEPTION_FLOOR, INTERCEPTION_NUMBER = 2, 2
FIELD_GOAL_DRAWS, FIELD_GOAL_ODDS, FIELD_GOAL_NEEDED = 5, 70, 3      # five Int(Rnd * 70) + 1 above the yard line, 3 needed
PUNT_ODDS, PUNT_SHORTEST = 35, 25                                   # Int(Rnd * 35) + 25 = 25 to 59 yards (0x443721)
RETURN_KIND_ODDS = 8                                                # Int(Rnd * 8) + 1 (0x445bb8)
RETURN_LONG_KIND, RETURN_SHORT_KIND = 6, 2                          # 6: range 90, 2: range 10, else 30
RETURN_RANGES = {RETURN_LONG_KIND: 90, RETURN_SHORT_KIND: 10}
RETURN_RANGE, RETURN_SHORTEST = 30, 12                              # Int(Rnd * range) + 12
TURNOVER_SPOT_ODDS, TURNOVER_SPOT_SHORTEST = 40, 5                  # Int(Rnd * 40) + 5 = 5 to 44 (0x44dfc8)


class Modifiers:
    """H8: the one door through which the engine reads the tables. Classic = NEUTRAL (everything unchanged)."""

    def run(self, offense: int, defense: int, entry: RunEntry) -> RunEntry:
        return entry

    def pass_(self, offense: int, defense: int, entry: PassEntry) -> PassEntry:
        return entry

    def fumble_odds(self, side: int) -> int:
        return FUMBLE_ODDS

    def field_goal_odds(self, side: int) -> int:
        return FIELD_GOAL_ODDS

    def punt(self, side: int) -> tuple[int, int]:
        return PUNT_ODDS, PUNT_SHORTEST

    def return_shortest(self, side: int, returner: int) -> int:
        """The shortest kick-off return of the receiving side's returner (nfl4 only, SX.8o: a Franchise game moves it by his rating)."""
        return RETURN_SHORTEST


NEUTRAL = Modifiers()
