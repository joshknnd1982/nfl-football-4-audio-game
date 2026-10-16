"""Rosters with ratings for the tests of the Franchise's ratings (nfl4 only, rule 0.13; SX.8b). This is inspired by Jim Kitchen.

`rated_roster` is a game roster (names as tests/pagrig.py `named_roster` makes them, a quarterback, and a rating for each of the
34 places keyed as the league keys them: (section heading, number)); `league_roster` takes the real league's `roster_for_game`.
`state_with` is a GameState with the fields the ratings read (the side with the ball, the ball carrier and the two tacklers).
"""
from nfl4.extras.franchise import data as D
from nfl4.game.gamestate import GameState
from pagrig import named_roster


# The design's start values (NFL_FRANCHISE_DESIGN 5.1, 5.2) with no team edge. The formulas are tested with these, so a later
# calibration of extras/tuning.py does not move a hand-worked number; the calibrated values have tests of their own.
DESIGN_VALUES = dict(FR_YARD_STEP=(12, 1), FR_SACK_STEP=(6, 3), FR_COMP_STEP=(6, 3), FR_FUM_STEP=(8, 3), FR_TEAM_EDGE=(0, 1),
                     FR_KICK_STEP=(5, 5), FR_PUNT_STEP=(8, 3), FR_SHIFT_MAX=6, FR_SHIFT_PER_SD=3, FR_SPREAD_FLOOR=78,
                     FR_PLAYOFF_PER_SD=60)


def use_design_values(monkeypatch) -> None:
    from nfl4.extras import tuning
    for name, value in DESIGN_VALUES.items():
        monkeypatch.setattr(tuning, name, value)


def rated_roster(prefix: str = "", rating: int = 70, **places):
    """Every place `rating`; `places` overrides by key `rb3=90`, `wr2=60`, `d5=40` (a defensive player), `qb=99`, `k=80`, `p=60`,
    `ret1=50`."""
    roster = named_roster(prefix)
    roster.quarterback = prefix + "QB"
    roster.ratings = {(heading, number): rating for heading, number, _ in D.PLACES}
    names = {"rb": "Running Backs:", "wr": "Receivers:", "d": "Defensive Players:", "ret": "Special Teams Players:",
             "k": "Kickers:", "p": "Kickers:", "qb": "Quarterback:"}
    for key, value in places.items():
        letters = key.rstrip("0123456789")
        number = int(key[len(letters):] or 1)
        if letters == "p":
            number = 2                      # the punter is kicker 2
        roster.ratings[(names[letters], number)] = value
    return roster


def state_with(own, opponent, wisoff=1, carrier=1, d1=1, d2=2, offense_play=1):
    """A GameState: the rosters of the two sides, `wisoff` has the ball, the play is `offense_play` (1 and 2 runs, 3 to 5
    passes, 8 to 10 quarterback runs) with the ball carrier or target `carrier` and the two tacklers `d1` and `d2`."""
    s = GameState()
    s.rosters = {1: own, 2: opponent}
    s.wisoff, s.defense = wisoff, 3 - wisoff
    s.carrier, s.defender1, s.defender2 = carrier, d1, d2
    s.offense_play = offense_play
    return s
