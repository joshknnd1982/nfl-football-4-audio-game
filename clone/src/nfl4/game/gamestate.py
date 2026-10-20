"""The state of one game: pag's variables in one record (GAME_SPEC 5.5; nfl4 hook H5). This is inspired by Jim Kitchen.

The original kept a game in about 120 local variables of pag (named by their frame offsets in the lifted text) and a few
form variables; everything but the result and the saved game was lost when pag ended. Here they are one record, each
field with the original's name next to it, so that a test can look at any of them, Save Game can write them in the
original's order (`saved_values`, the file itself is S7.5) and the extras can copy the whole record (`snapshot`, a
challenge's state before the play, NFL_EXTRAS_DESIGN 6.4). `extras` is None in Classic and the engine never reads it.

Sides: 1 = the player's team, 2 = the opponent. The ball: `half` (Lcc) is the half it is in (1 = the opponent's half,
2 = the player's half) and `yard_line` (L5b8) its distance to that half's goal line, 0 to 50.
"""
from __future__ import annotations

import copy
from dataclasses import dataclass, field

from .phrases import GroupedPhrases, PhraseHistory
from .setup import Roster


def other(side: int) -> int:
    return 2 if side == 1 else 1


def own_half(side: int) -> int:
    """The half a side defends: side 1's own half is half 2, side 2's is half 1."""
    return 2 if side == 1 else 1


@dataclass
class SideStats:
    """One side's numbers (the arrays with index 1 and 2): the statistics of 4.19 and the score."""
    pass_attempts: int = 0       # L8d0 (sacks included, Q20)
    completions: int = 0         # L854
    passing_yards: int = 0       # L294 (sacks subtract)
    sacked: int = 0              # L680
    intercepted: int = 0         # Lf8
    running_plays: int = 0       # L744
    running_yards: int = 0       # L7b8
    fumbles_lost: int = 0        # L464
    first_downs: int = 0         # L278 (kick-off returns too, Q19)
    score: int = 0               # L8ec
    interception_count: int = 0  # L8c: +3 per pass, 0 after an interception; not saved (Q28)

    def stat_values(self) -> list[int]:
        """The eleven numbers of the quarter statistics, in their spoken order (4.19)."""
        return [self.pass_attempts, self.completions, self.passing_yards, self.sacked, self.intercepted,
                self.running_plays, self.running_yards, self.fumbles_lost, self.passing_yards + self.running_yards,
                self.first_downs, self.score]


@dataclass
class SavedGame:
    """football.sav's values in the original's order (GAME_SPEC 12; read 0x43afb7 to 0x43b80c, written 0x45f669 to
    0x45ff26) plus D-027's opening receiver after them. The file is S7.5; this is what it holds."""
    wisoff: int
    defense: int                      # L504
    half: int                         # Lcc (written twice by the original; the second value is the one that counts)
    quarter: int                      # L3c0
    counter: int                      # L738
    plays: list[int]                  # L2cc(1 to 5)
    countdown: float                  # CountDown
    stats: dict[int, SideStats]       # the 22 values L8d0 to L8ec, side 1 then 2 for each
    yard_line: int                    # L5b8
    down: int                         # L3b0
    to_go: int                        # L82c
    opponent_quarterback: str         # Me.m2b8(2), as its length and the character codes
    opening_receiver: int | None = None   # L158, the clone's added value (D-027 item 3); None in an original file
    # nfl4 only (rule 0.13, NFL_EXTRAS_DESIGN 12.3, SX.2): a game played with the N. F. L. rules writes its extras record
    # after them (a marker, a format number, one JSON string). extras_marked: the marker was there; extras: the JSON text,
    # None when there was none or it could not be read (then the extras start from their start values, C10)
    extras: str | None = None
    extras_marked: bool = False
    # nfl4 only (SX.14, rule 0.23, playbook 7.17): two more sections after the extras. `info` is the one-sentence summary's facts (the
    # teams, the week, the date, the time left; JSON), `resume` the rest of the engine's state that an automatic save keeps so a
    # crashed game goes on with the same draws (JSON). None in a file of the original and in a save made without them.
    info: str | None = None
    resume: str | None = None


@dataclass
class GameState:
    # possession and the ball (5.5)
    wisoff: int = 1                    # the side on offense (a form variable; say3 reads the Game's copy)
    defense: int = 2                   # L504
    half: int = 2                      # Lcc
    yard_line: int = 0                 # L5b8
    down: int = 1                      # L3b0
    to_go: int = 10                    # L82c
    # time
    quarter: int = 1                   # L3c0: 1 to 4, 5 for every overtime period (6 after the game)
    counter: int = 1                   # L738: the play counter of the period
    plays: list[int] = field(default_factory=lambda: [30] * 5)   # L2cc(1 to 5)
    overtime: int = 0                  # L238
    opening_receiver: int | None = None    # L158 (None = Empty)
    first_kickoff: bool = True         # L8a8 = 1: the next kick-off records L158
    # the play
    offense_play: int = 0              # L1d4 (0 at a kick-off)
    defense_play: int = 1              # L1c4
    previous_play: int = 0             # L598
    repeats: int = 0                   # L148
    two_point: bool = False            # L81c
    carrier: int = 1                   # L408 (ball carrier or target, 1 to 6)
    defender1: int = 1                 # L578
    defender2: int = 2                 # L664
    yards: int = 0                     # L32c
    tackle_sound: int = 0              # L4f0
    tackle_sentence: str = ""          # L26c
    text: str = ""                     # L4f4: the sentence being built
    play_kind: int = 0                 # L6e4: 1 run, 2 pass
    result_kind: str = ""              # the kind of the play's result (outcome.py), for the H2 record
    qb_run: str = ""                   # nfl4 only (SX.5): "sneak", "keeper", "draw" or "scramble" while such a play is run
    slid: bool = False                 # nfl4 only (SX.5): the quarterback slid at the end of the run
    returner: int = 1                  # L898 of the kick-off: which special teams player catches it
    points: int = 0                    # L79c
    # flags of the original's paths
    punt_flag: int = 0                 # L1b4: 1 after a punt's kick, 2 while its possession sentence is spoken
    return_flag: bool = False          # L30c: no pause before the tackle of a kick-off return
    downs_flag: bool = False           # L538
    interception_flag: bool = False    # L634
    fumble_flag: bool = False          # L118
    try_good: bool = False             # L614
    gpn: int = 0                       # Me.gpn: 1 when footplay.txt was read
    # names: Me.m430 the teams, Me.m2b8 the quarterbacks, Me.m468 the He or She words, the rosters, L480
    teams: dict[int, str] = field(default_factory=dict)
    quarterbacks: dict[int, str] = field(default_factory=dict)
    he_she: dict[int, str] = field(default_factory=lambda: {1: " He ", 2: " He ", 3: " He ", 4: " He "})
    rosters: dict[int, Roster] = field(default_factory=dict)
    banter_names: list[str] = field(default_factory=list)
    # statistics and score
    stats: dict[int, SideStats] = field(default_factory=lambda: {1: SideStats(), 2: SideStats()})
    # the phrase histories (one game, not saved, Q37)
    snap_history: PhraseHistory = field(default_factory=lambda: PhraseHistory(6))        # L3e8
    sack_history: PhraseHistory = field(default_factory=lambda: PhraseHistory(4))        # L218
    throw_history: PhraseHistory = field(default_factory=lambda: PhraseHistory(4))       # L2b0
    incomplete_history: PhraseHistory = field(default_factory=lambda: PhraseHistory(6))  # L5d4
    catch_history: PhraseHistory = field(default_factory=lambda: PhraseHistory(6))       # L1fc
    handoff: GroupedPhrases = field(default_factory=lambda: GroupedPhrases(4, 9, "hand-off"))     # L70, L4a0
    dropback: GroupedPhrases = field(default_factory=lambda: GroupedPhrases(3, 11, "drop-back"))  # L164, L438
    last_return_run: int = 0           # L558
    banter_used: list[int] = field(default_factory=list)   # L8b4(1 to L7dc)
    # the end
    final_scores: tuple[int, int] | None = None   # Me.m414(1), (2)
    finished: bool = False             # pag passed the period-end flow (L194 = 1)
    # NFL_EXTRAS_DESIGN 3 H5: the extras' own state; None in Classic
    extras: object = None

    def score(self, side: int) -> int:
        return self.stats[side].score

    def plays_in(self, quarter: int) -> int:
        """L2cc(quarter): quarters 1 to 4, then 5 for every overtime period."""
        return self.plays[min(quarter, 5) - 1]

    def in_own_half(self) -> bool:
        """The ball is in the offense's own half: (Lcc 1 and wisoff 2) or (Lcc 2 and wisoff 1)."""
        return self.half == own_half(self.wisoff)

    def snapshot(self) -> "GameState":
        """A full copy (H5): the extras keep it from before the apply step until the next snap."""
        return copy.deepcopy(self)

    def saved(self, countdown: float) -> SavedGame:
        """What Save Game writes (the order of the original's Put statements), with D-027's opening receiver and, with the
        N. F. L. rules, the extras record (H5; None in Classic, so a Classic save is the S7.5 file byte for byte)."""
        extras = self.extras.to_json() if self.extras is not None else None
        return SavedGame(self.wisoff, self.defense, self.half, self.quarter, self.counter, list(self.plays), countdown,
                         copy.deepcopy(self.stats), self.yard_line, self.down, self.to_go, self.quarterbacks.get(2, ""),
                         self.opening_receiver, extras, extras is not None)

    def load(self, saved: SavedGame) -> None:
        """The reads of a loaded game (0x43afb7 to 0x43b80c). The interception counts restart (Q28) and M2W, M4W and M5W
        keep the values the set-up drew; L158 comes back when the file has it, else the original's rule applies."""
        self.wisoff, self.defense, self.half = saved.wisoff, saved.defense, saved.half
        self.quarter, self.counter, self.plays = saved.quarter, saved.counter, list(saved.plays)
        for side in (1, 2):
            values = copy.deepcopy(saved.stats[side])
            values.interception_count = 0
            self.stats[side] = values
        self.yard_line, self.down, self.to_go = saved.yard_line, saved.down, saved.to_go
        self.quarterbacks[2] = saved.opponent_quarterback
        if saved.opening_receiver is not None:
            self.opening_receiver = saved.opening_receiver
            self.first_kickoff = False
        if self.extras is not None:                     # N. F. L. rules (H5): the save's record, or the start values
            self.extras.load_saved(saved, self)
