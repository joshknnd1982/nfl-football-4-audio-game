"""The set-up of a game: the rosters, the players' names, the quarter lengths and the fixed word lists. This is inspired by Jim Kitchen.

GAME_SPEC 5.5 "Set-up" and 11 (CODE (lifted) pag's GoSub 0x453eac, read in full in S3.5; every constant checked against the
asm by `tools/vb6_const_check.py`, the 9 Rnd draws by `tools/vb6_rnd_check.py`). The order of the random draws is part of
the original and is kept, so a scripted source reproduces any game:

1. the player's own team (side 1): the 33 names come from footplay.txt when it is valid (S7.5 reads and checks the file and
   hands the names over as a Roster), else 33 drawn without replacement in the order Running Backs 6, Receivers 6,
   Defensive Players 17, Special Teams Players 2, Kickers 2 (kicker 1, then kicker 2), which S7.5 writes to the file in the
   same order. Every name read from the file blanks the FIRST equal pool entry (exact case); a name that is not in the pool
   blanks nothing.
2. the opponent (side 2): the same 33 draws, never stored (new names at every game, Q39).
3. the plays of the five periods L2cc(1 to 5) = Int(Rnd * 8) + 30 (30 to 37; quarters 1 to 4 and every overtime period),
   then the three two-minute-warning lengths M2W, M4W, M5W = Int(Rnd * 3) + 5.
Also set: quarter 1, CountDown 100, play counter 1.

The list of the players' names L480 (GAME_SPEC 5.13, the original's banter names) gets the running backs, receivers and defensive
players, in this order: the player's 29, then the opponent's 29 (58 names; special teams players and kickers are never in it). BC.2
(D-180): the original's banter is gone; the list stays as `player_names` for the remark lines that name a player (extras/remarks.py). The quarterbacks come
later from Getqbs (4.12). The rosters are two-dimensional in the original (side, number); here `rosters[side]`.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .names import NamePool
from .rnd import GameRandom

# The sections of footplay.txt, in the order the file has them (GAME_SPEC 11; strings 2304 to 2308) with their counts
HEADINGS = ("Running Backs:", "Receivers:", "Defensive Players:", "Special Teams Players:", "Kickers:")
COUNTS = (6, 6, 17, 2, 2)
QUARTERBACK_HEADING = "Quarterback:"                     # string 797, appended by Getqbs
PERIODS = 5                                               # L2cc(1 to 5): quarters 1 to 4 and every overtime period

# The ten snap-count words and the seven run directions the set-up fills (GAME_SPEC 5.8, 5.9; strings 2309 and others)
SNAP_WORDS = (" Red ", " Right ", " Blue ", " Left ", " white ", " black ", " green ", " chrome ", " X ", " XP ")
RUN_DIRECTIONS = ("up the middle", "on the left side", "on the right side", "around the right side",
                  "around the left side", "around the left end", "around the right end")
# The play menus' items (GAME_SPEC 4.15; strings 2289 to 2303)
OFFENSE_ITEMS = (" 1. Line Plunge ", " 2. End Run ", " 3. Screen Pass ", " 4. Short Pass ", " 5. Long Pass ",
                 " 6. Field Goal ", " 7. Punt ", " 8. Save Game ")
DEFENSE_ITEMS = (" 1. Goal Line ", " 2. Short Run ", " 3. Long Run ", " 4. Blitz ", " 5. Short Pass ", " 6. Long Pass ",
                 " 7. Save Game ")


@dataclass
class Roster:
    """One side's 33 names. kickers[0] is kicker 1 (field goals, extra points, kick-offs), kickers[1] kicker 2 (the
    holder and punter); special_teams are the two returners."""
    running_backs: list[str] = field(default_factory=list)
    receivers: list[str] = field(default_factory=list)
    defense: list[str] = field(default_factory=list)
    special_teams: list[str] = field(default_factory=list)
    kickers: list[str] = field(default_factory=list)
    # The last item of footplay.txt (Getqbs reads the file with Input # to its end: normally the name after
    # "Quarterback:"); S7.5 fills it when it reads the file, "" otherwise. Not one of the 33 names.
    quarterback: str = ""
    # NFL_EXTRAS_DESIGN 3 H7 (nfl4 only): a rating per slot, keyed (section heading, number 1 to n), for the Franchise
    # mode (SX.8). Empty, and never read, in Classic.
    ratings: dict = field(default_factory=dict)
    # nfl4 only (SR.4, design 21.4 (2)): the places of the real roster's view that have nobody (a team with three backs has no fourth), keyed like
    # `ratings`; such a place carries its cover's name and gets no share of the usage draw. Empty, and never read, in Classic.
    empty: list = field(default_factory=list)

    def sections(self) -> list[tuple[str, list[str]]]:
        """(heading, names) in the order of footplay.txt."""
        return list(zip(HEADINGS, (self.running_backs, self.receivers, self.defense, self.special_teams, self.kickers)))

    def names(self) -> list[str]:
        return [name for _, names in self.sections() for name in names]

    def is_complete(self) -> bool:
        return all(len(names) == count for (_, names), count in zip(self.sections(), COUNTS))


@dataclass
class GameSetup:
    rosters: dict[int, Roster]                   # side 1 = the player's team, side 2 = the opponent
    player_names: list[str]                      # L480: 58 names (BC.2: was banter_names)
    plays_per_period: list[int]                  # L2cc(1 to 5)
    warnings: tuple[int, int, int]               # M2W, M4W, M5W
    own_names_drawn: bool                        # True: footplay.txt has to be written (the 33 names are new)
    quarter: int = 1                             # L3c0
    countdown: int = 100                         # CountDown
    play_counter: int = 1                        # L738

    def plays_in(self, period: int) -> int:
        """L2cc(period): the plays of quarter 1 to 4 (or of an overtime period: 5)."""
        return self.plays_per_period[min(period, PERIODS) - 1]


def draw_roster(pool: NamePool, player_names: list[str] | None) -> Roster:
    """33 names drawn without replacement in the original's order. The running backs, receivers and defensive players
    also go to `player_names` when it is given (the original adds them for both sides)."""
    roster = Roster()
    for _ in range(COUNTS[0]):
        roster.running_backs.append(pool.take())
    for _ in range(COUNTS[1]):
        roster.receivers.append(pool.take())
    for _ in range(COUNTS[2]):
        roster.defense.append(pool.take())
    for _ in range(COUNTS[3]):
        roster.special_teams.append(pool.take())
    for _ in range(COUNTS[4]):
        roster.kickers.append(pool.take())
    if player_names is not None:
        player_names.extend(roster.running_backs + roster.receivers + roster.defense)
    return roster


def adopt_roster(pool: NamePool, names: Roster, player_names: list[str] | None) -> Roster:
    """The player's names read from footplay.txt: each blanks the first equal pool entry, in file order. A roster with ratings (a
    Franchise team, nfl4 only, SX.8b) is the league's: its names are not the pool's to take, so it blanks nothing."""
    if not names.is_complete():
        raise ValueError("a roster of the file has to hold 6, 6, 17, 2 and 2 names")
    if not names.ratings:
        for name in names.names():
            pool.blank_exact(name)
    if player_names is not None:
        player_names.extend(names.running_backs + names.receivers + names.defense)
    # H7 (nfl4 only, SX.8b): the ratings of a roster that has them (a Franchise team) come along, and its quarterback; the file's
    # rosters have no ratings, and their quarterback (footplay.txt's last item) is carried but only Getqbs reads it, from
    # `own_names`: Classic does not change
    return Roster(list(names.running_backs), list(names.receivers), list(names.defense), list(names.special_teams),
                  list(names.kickers), quarterback=names.quarterback, ratings=dict(names.ratings))


def adopt_opponent(names: Roster, player_names: list[str] | None) -> Roster:
    """H7 (nfl4 only, SX.8b; never in Classic): the opponent of a Franchise game is a team of the league with its own players and
    ratings, handed in as a Roster. No name is drawn and the pool is not touched; the names go to the list of players' names as a
    drawn roster's do."""
    if not names.is_complete():
        raise ValueError("a roster of the league has to hold 6, 6, 17, 2 and 2 names")
    if player_names is not None:
        player_names.extend(names.running_backs + names.receivers + names.defense)
    return Roster(list(names.running_backs), list(names.receivers), list(names.defense), list(names.special_teams),
                  list(names.kickers), quarterback=names.quarterback, ratings=dict(names.ratings))


def adopt_partial_roster(pool: NamePool, names: Roster, player_names: list[str] | None) -> Roster:
    """footplay.txt with a wrong or missing part (S7.5, D-025 d: only the broken part is repaired): the sections that hold
    their full number of names are kept (each name blanks the first equal pool entry, in file order), the others are drawn
    in the original's order, and the quarterback of the file stays. The roster then differs from the file, so the set-up
    says the file has to be written again."""
    sections = [section for _, section in names.sections()]
    for section, count in zip(sections, COUNTS):
        if len(section) == count:
            for name in section:
                pool.blank_exact(name)
    parts = [list(section) if len(section) == count else [pool.take() for _ in range(count)]
             for section, count in zip(sections, COUNTS)]
    roster = Roster(*parts, quarterback=names.quarterback)
    if player_names is not None:
        player_names.extend(roster.running_backs + roster.receivers + roster.defense)
    return roster


def new_game_setup(rnd: GameRandom, pool: NamePool, own_names: Roster | None = None,
                   opponent_names: Roster | None = None) -> GameSetup:
    """pag's set-up GoSub: the own roster (from the file when `own_names` is given, else drawn), the opponent's, the
    periods' lengths and the three warning lengths, each in the original's order. `opponent_names` (nfl4 only, SX.8b: the
    Franchise's league team) is the opponent's roster instead of the 33 draws; None is the original."""
    player_names: list[str] = []
    if own_names is not None and own_names.is_complete():
        own = adopt_roster(pool, own_names, player_names)
    elif own_names is not None:
        own = adopt_partial_roster(pool, own_names, player_names)
    else:
        own = draw_roster(pool, player_names)
    opponent = draw_roster(pool, player_names) if opponent_names is None else adopt_opponent(opponent_names, player_names)
    plays = [rnd.below(8) + 30 for _ in range(PERIODS)]
    warnings = (rnd.below(3) + 5, rnd.below(3) + 5, rnd.below(3) + 5)
    return GameSetup({1: own, 2: opponent}, player_names, plays, warnings, own_names is None or not own_names.is_complete())
