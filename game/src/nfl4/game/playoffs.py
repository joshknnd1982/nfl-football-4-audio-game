"""The play-off picture: the score table, a computer game, the division winners, the wild cards, the seeds and the
bracket's files. This is inspired by Jim Kitchen.

GAME_SPEC 5.14 to 5.17 and 12 (CODE (lifted) pog p_4615b0 and finplay17 p_47d8b0). No speech, sound or file code is in
this module: the season engine (game/season_engine.py) speaks what these functions work out. A team is a `TeamRef`
(division 1 to 8, place 1 to 4); divisions 1 to 4 are the A. F. C., 5 to 8 the N. F. C.

The original keeps the pairings of the coming round in footbal4.dat (records of four numbers: division and place of the
visitor, division and place of the home team) and the four teams with a bye in footbal5.dat (A. F. C. D3, D4, N. F. C.
D3, D4); `PlayoffState` is that data in memory with the file values for S7.5.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, NamedTuple, Sequence

from .league import DIVISIONS, PLACES
from .rnd import GameRandom
from .standings import Records, half_losses, half_wins

# The 32-entry score table of pog (L1c8) and finplay17 (Ld4), 0x4619e7 to 0x46250b and 0x47da77 to 0x47df39: scores 0, 3, 6,
# 7, 9, 10, 12 and 14 have two entries, 20 two, 21 three, so a draw of an index is not a draw of a score.
SCORE_TABLE = (0, 0, 3, 3, 6, 6, 7, 7, 9, 9, 10, 10, 12, 12, 14, 14, 17, 20, 20, 21, 21, 21, 24, 28, 31, 35, 38, 41, 42,
               45, 49, 51)

AFC_DIVISIONS = (1, 2, 3, 4)
NFC_DIVISIONS = (5, 6, 7, 8)


class TeamRef(NamedTuple):
    division: int
    place: int


Pairing = tuple[TeamRef, TeamRef]        # (visitor, home): the first team of a footbal4.dat record is the visitor


def score_of(index: int) -> int:
    """T(index) for an index 1 to 32."""
    return SCORE_TABLE[index - 1]


def original_sort(items: Sequence, key: Callable) -> list:
    """The original's insertion sort (every sort of pog is this loop): for outer = 1 to n - 1, inner = outer down to 1, the
    next item moves ahead of the previous one only when its key is LESS (an equal key stops the inner loop), so it is
    stable and ascending, fewest first."""
    items = list(items)
    for outer in range(1, len(items)):
        for inner in range(outer, 0, -1):
            if key(items[inner]) >= key(items[inner - 1]):
                break
            items[inner - 1], items[inner] = items[inner], items[inner - 1]
    return items


# ----- a computer game (pog's play-off weeks and finplay17, 5.17 item 2, Q45) -----

@dataclass(frozen=True)
class ComputerGame:
    first_wins: bool            # Int(Rnd * 2) + 1 = 1: the visitor (the first team of the record) wins
    winner_index: int           # an index of the score table whose score is not 0
    loser_index: int            # an index whose score is lower than the winner's

    @property
    def winner_score(self) -> int:
        return score_of(self.winner_index)

    @property
    def loser_score(self) -> int:
        return score_of(self.loser_index)


def computer_game(rnd: GameRandom, first_wins: Callable[[GameRandom], bool] | None = None) -> ComputerGame:
    """The draws of one computer game in the lifted order: the coin Int(Rnd * 2) + 1, the winner's index Int(Rnd * 32) + 1
    drawn again while its score is 0, the loser's index drawn again while its score is not lower (every Rnd of the
    original multiplies a constant: nothing needs a Single, B-P45; the redraws are bounded, G-D1). `first_wins` (H14's
    `playoff_first_wins`, nfl4 only) decides the coin instead of `rnd(2) == 1`: the Franchise leans it by strength."""
    coin = rnd(2) if first_wins is None else (1 if first_wins(rnd) else 2)
    winner = rnd.redraw(lambda: rnd(32), lambda i: score_of(i) != 0,
                        lambda: next(i for i in range(1, 33) if score_of(i) != 0), "a play-off game's winning score")
    loser = rnd.redraw(lambda: rnd(32), lambda i: score_of(i) < score_of(winner),
                       lambda: next(i for i in range(1, 33) if score_of(i) < score_of(winner)),
                       "a play-off game's losing score")
    return ComputerGame(coin == 1, winner, loser)


# ----- the season's play-off files in memory (footbal4.dat and footbal5.dat) -----

@dataclass
class PlayoffState:
    pairings: list[Pairing] = field(default_factory=list)     # footbal4.dat: the coming round's games
    byes: list[TeamRef] = field(default_factory=list)         # footbal5.dat: A. F. C. D3, D4, N. F. C. D3, D4

    def clear(self) -> None:
        self.pairings.clear()
        self.byes.clear()

    def pairing_values(self) -> list[int]:
        """The values of footbal4.dat: division and place of the visitor, then of the home team, per game."""
        values: list[int] = []
        for visitor, home in self.pairings:
            values.extend((visitor.division, visitor.place, home.division, home.place))
        return values

    def bye_values(self) -> list[int]:
        values: list[int] = []
        for team in self.byes:
            values.extend((team.division, team.place))
        return values

    @staticmethod
    def pairings_from_values(values: Sequence[int]) -> list[Pairing]:
        values = [int(v) for v in values]
        if len(values) % 4:
            raise ValueError("footbal4.dat holds %d values, not a whole number of games" % len(values))
        return [(TeamRef(*values[i:i + 2]), TeamRef(*values[i + 2:i + 4])) for i in range(0, len(values), 4)]

    @staticmethod
    def byes_from_values(values: Sequence[int]) -> list[TeamRef]:
        values = [int(v) for v in values]
        if len(values) % 2:
            raise ValueError("footbal5.dat holds %d values, not whole teams" % len(values))
        return [TeamRef(*values[i:i + 2]) for i in range(0, len(values), 2)]

    def contains_player(self, own: TeamRef) -> bool:
        return any(own in pairing for pairing in self.pairings)

    def opponent_of(self, own: TeamRef) -> tuple[TeamRef, int] | None:
        """Form_Load step 7c (GAME_SPEC 3): the player's opponent and vtrnt: the player is the visitor (the first team):
        the opponent is the second and vtrnt = 2; the player is the home team: the opponent is the first and vtrnt = 1.
        The original reads every record and keeps the last match."""
        found = None
        for visitor, home in self.pairings:
            if visitor == own:
                found = (home, 2)
            elif home == own:
                found = (visitor, 1)
        return found


# ----- the end of the regular season (pog after week 16, 5.15) -----

@dataclass(frozen=True)
class Qualifier:
    """A team with the record that is SPOKEN for it. For a wild card that was replaced by the player's team (Q43) the
    record is the replaced team's, which has as many wins as the player's team."""
    team: TeamRef
    wins: int
    losses: int
    ties: int = 0               # nfl4 only (SX.12): the N. F. L. rules mode's regular-season ties; always 0 in Classic


def _own_wins(records: Records, own: TeamRef) -> int:
    return half_wins(records.record(own.division, own.place)[0], records.ties_of(own.division, own.place))


def division_winners(records: Records, own: TeamRef) -> tuple[list[Qualifier], bool]:
    """Divisions 1 to 8: the four teams ordered by LOSSES, fewest first (the wins are not looked at); the first is the
    winner, its record the one spoken. In the player's division, when the player's team is not first but has as many WINS
    as the first, the player's team is the winner instead (Q43; the record spoken stays the first team's). Returns the
    winners in division order and the flag L180: the player's team is a division winner. A tie counts half a loss and half a win
    (SX.12; no team of a Classic season has one, so the order is the original's)."""
    winners: list[Qualifier] = []
    in_playoffs = False
    for division in range(1, DIVISIONS + 1):
        teams = [(place,) + records.record(division, place) + (records.ties_of(division, place),) for place in range(1, PLACES + 1)]
        ordered = original_sort(teams, key=lambda t: half_losses(t[2], t[3]))
        place, wins, losses, ties = ordered[0]
        if division == own.division:
            if place == own.place:
                in_playoffs = True
            elif _own_wins(records, own) == half_wins(wins, ties):
                place = own.place
                in_playoffs = True
        winners.append(Qualifier(TeamRef(division, place), wins, losses, ties))
    return winners, in_playoffs


def seeds(winners: Sequence[Qualifier], conference: Sequence[int]) -> list[Qualifier]:
    """The conference's four division winners ordered by WINS, fewest first (an equal number keeps the division order
    North, East, West, South): D1 (the fewest wins, hosts the first wild card) to D4 (the most wins, a bye). A tie is half a win."""
    return original_sort([winners[d - 1] for d in conference], key=lambda q: half_wins(q.wins, q.ties))


def wild_cards(records: Records, conference: Sequence[int], winners: Sequence[Qualifier], own: TeamRef,
               in_playoffs: bool, count: int = 2) -> tuple[list[Qualifier], bool]:
    """The conference's 16 teams in division and place order, the four division winners given 0 wins and 20 losses so they
    come last, ordered by LOSSES, fewest first; the first two are the wild cards. When the player's team is neither a
    division winner (in_playoffs) nor one of the two, is in this conference and has as many wins as the second wild card,
    it takes the second's place (Q43). Returns the two and the updated flag. `count` (nfl4 only, D-129) is 3 for the N. F. L.'s
    14-team play-offs: the first three, and Q43's place is the third's (the last one)."""
    candidates = []
    for division in conference:
        for place in range(1, PLACES + 1):
            wins, losses = records.record(division, place)
            ties = records.ties_of(division, place)
            if winners[division - 1].team.place == place:
                wins, losses, ties = 0, 20, 0
            candidates.append(Qualifier(TeamRef(division, place), wins, losses, ties))
    ordered = original_sort(candidates, key=lambda q: half_losses(q.losses, q.ties))
    cards = list(ordered[:count])
    for card in cards:
        if card.team == own:
            in_playoffs = True
    last = cards[-1]
    if not in_playoffs and own.division in conference and _own_wins(records, own) == half_wins(last.wins, last.ties):
        cards[-1] = Qualifier(own, last.wins, last.losses, last.ties)
        in_playoffs = True
    return cards, in_playoffs


@dataclass(frozen=True)
class RegularSeasonEnd:
    winners: list[Qualifier]                  # the eight division winners in division order (with the spoken records)
    afc_wild_cards: list[Qualifier]
    nfc_wild_cards: list[Qualifier]
    afc_seeds: list[Qualifier]                # D1 to D4
    nfc_seeds: list[Qualifier]
    pairings: list[Pairing]                   # footbal4.dat: the wild card games
    byes: list[TeamRef]                       # footbal5.dat
    player_in_playoffs: bool                  # L180
    seed_of: dict = field(default_factory=dict)   # nfl4 only (D-129): the N. F. L. bracket's seeds 1 to 7 of each conference; empty for the original's

    def where(self, own: TeamRef) -> str:
        """pog's test after the files are written (0x46f321): the player's team is in a wild card game ("wild_card"), has a
        bye ("bye") or is out ("out")."""
        if any(own in pairing for pairing in self.pairings):
            return "wild_card"
        if own in self.byes:
            return "bye"
        return "out"


def end_of_regular_season(records: Records, own: TeamRef) -> RegularSeasonEnd:
    winners, in_playoffs = division_winners(records, own)
    afc_seeds = seeds(winners, AFC_DIVISIONS)
    nfc_seeds = seeds(winners, NFC_DIVISIONS)
    afc_cards, in_playoffs = wild_cards(records, AFC_DIVISIONS, winners, own, in_playoffs)
    nfc_cards, in_playoffs = wild_cards(records, NFC_DIVISIONS, winners, own, in_playoffs)
    pairings = [(afc_cards[0].team, afc_seeds[0].team), (afc_cards[1].team, afc_seeds[1].team),
                (nfc_cards[0].team, nfc_seeds[0].team), (nfc_cards[1].team, nfc_seeds[1].team)]
    byes = [afc_seeds[2].team, afc_seeds[3].team, nfc_seeds[2].team, nfc_seeds[3].team]
    return RegularSeasonEnd(winners, afc_cards, nfc_cards, afc_seeds, nfc_seeds, pairings, byes, in_playoffs)


# ----- the N. F. L.'s 14-team play-offs (nfl4 only, rule 0.13; D-129, the owner's answer to Q-061) -----
#
# A franchise that plays the real calendar has the N. F. L.'s play-offs (NFL Rule Book, the playoff format since 2020, SRC-OFFICIAL): 7 teams a
# conference, the four division winners seeded 1 to 4 and three wild cards 5 to 7; only seed 1 has a bye; in the wild card round 2 hosts 7, 3 hosts 6
# and 4 hosts 5; the division round is reseeded (seed 1 hosts the lowest seed left, the other two winners meet at the better seed), and the better
# seed hosts the conference championship. The order of the teams is the original's own rule (wins, a tie half a win; equal teams keep the division
# order; the losses for the wild cards; Q43's place for the player's team): the N. F. L.'s long list of tie-breakers is not modelled. Classic and a
# franchise on the original's 16 weeks keep the original's 12 teams exactly (the golden transcript).

REAL_WILD_CARDS = 3                       # a conference's wild cards: seeds 5, 6 and 7
REAL_BYES = 2                             # the two seeds 1, A. F. C. then N. F. C.
REAL_WILD_CARD_GAMES = 6                  # three a conference
CLASSIC_BYES = 4
CLASSIC_WILD_CARD_GAMES = 4


def real_seeds(winners: Sequence[Qualifier], conference: Sequence[int]) -> list[Qualifier]:
    """The conference's four division winners as seeds 1 to 4: the most wins first (a tie is half a win), equal wins in the division order."""
    return original_sort([winners[d - 1] for d in conference], key=lambda q: -half_wins(q.wins, q.ties))


def _real_games(seeds_: Sequence[Qualifier], cards: Sequence[Qualifier]) -> list[Pairing]:
    """A conference's wild card games (visitor, home): seed 7 at 2, seed 6 at 3, seed 5 at 4."""
    return [(cards[2].team, seeds_[1].team), (cards[1].team, seeds_[2].team), (cards[0].team, seeds_[3].team)]


def real_end_of_regular_season(records: Records, own: TeamRef) -> RegularSeasonEnd:
    """The end of a regular season on the real calendar: the eight division winners (the original's rule), the seeds, three wild cards a
    conference, the six wild card games (A. F. C. first) and the two teams with a bye (the A. F. C.'s seed 1, then the N. F. C.'s)."""
    winners, in_playoffs = division_winners(records, own)
    afc_seeds = real_seeds(winners, AFC_DIVISIONS)
    nfc_seeds = real_seeds(winners, NFC_DIVISIONS)
    afc_cards, in_playoffs = wild_cards(records, AFC_DIVISIONS, winners, own, in_playoffs, REAL_WILD_CARDS)
    nfc_cards, in_playoffs = wild_cards(records, NFC_DIVISIONS, winners, own, in_playoffs, REAL_WILD_CARDS)
    pairings = _real_games(afc_seeds, afc_cards) + _real_games(nfc_seeds, nfc_cards)
    byes = [afc_seeds[0].team, nfc_seeds[0].team]
    seed_of: dict = {}
    for seeds_, cards in ((afc_seeds, afc_cards), (nfc_seeds, nfc_cards)):
        for number, q in enumerate(list(seeds_) + list(cards), start=1):
            seed_of[q.team] = number
    return RegularSeasonEnd(winners, afc_cards, nfc_cards, afc_seeds, nfc_seeds, pairings, byes, in_playoffs, seed_of)


def _by_seed(teams: Sequence[TeamRef], seed_of: dict) -> list[TeamRef]:
    """The teams, the best seed first (a team the seeds do not know comes last: a damaged state still gives a whole round)."""
    return sorted(teams, key=lambda team: seed_of.get(team, 99))


def real_division_pairings(winners: Sequence[TeamRef], byes: Sequence[TeamRef], seed_of: dict) -> list[Pairing]:
    """The division round after the six wild card games (their winners in game order, the A. F. C.'s three first): in each conference seed 1 hosts
    the lowest seed left, and the other two winners meet at the better seed. Four games, the A. F. C.'s two first."""
    out: list[Pairing] = []
    for conference_winners, top in ((winners[:3], byes[0]), (winners[3:6], byes[1])):
        best, middle, lowest = _by_seed(conference_winners, seed_of)
        out += [(lowest, top), (middle, best)]
    return out


def real_championship_pairings(winners: Sequence[TeamRef], seed_of: dict) -> list[Pairing]:
    """The two conference championships after the division round (its four winners in game order): the better seed hosts."""
    out: list[Pairing] = []
    for pair in (winners[:2], winners[2:4]):
        better, worse = _by_seed(pair, seed_of)
        out.append((worse, better))
    return out
