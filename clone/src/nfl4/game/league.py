"""The 32 teams and 8 divisions in memory. This is inspired by Jim Kitchen.

GAME_SPEC 11 and 5.2 (CODE (lifted) GetTeams p_4321d0 and SayStand): a team is the pair (division 1 to 8, place 1 to 4);
the original keeps the nicknames in one array at index division + 9 * place and the division texts in another. The
player's own team is (tn1, tn2) and this week's opponent (tn3, tn4). Only nicknames, no cities. The spellings are written
for the speech engine ("Forty Niners", "Sea hawks") and kept exactly.

S7.7 builds a League from the player's files teams.txt and divisions.txt (IDs T01 to T32 and D1 to D8 in this order,
CUSTOMIZABLE_CONTENT 3 and 4); the defaults below are the original data. A division's file value has no surrounding
spaces; the program adds them, as the original's texts have them (" A. F. C. North. ").
"""
from __future__ import annotations

DIVISIONS = 8
PLACES = 4
TEAM_COUNT = DIVISIONS * PLACES

# T01 to T32: division 1 places 1 to 4, division 2 places 1 to 4, ... (GAME_SPEC 11; strings 802 to 823, s48 to s54)
DEFAULT_TEAM_NAMES = (
    "Bengals", "Browns", "Ravens", "Steelers",             # A. F. C. North
    "Bills", "Dolphins", "Jets", "Patriots",               # A. F. C. East
    "Broncos", "Chargers", "Chiefs", "Raiders",            # A. F. C. West
    "Colts", "Jaguars", "Texans", "Titans",                # A. F. C. South
    "Bears", "Lions", "Packers", "Vikings",                # N. F. C. North
    "Cowboys", "Eagles", "Giants", "Redskins",             # N. F. C. East
    "Cardinals", "Forty Niners", "Rams", "Sea hawks",      # N. F. C. West
    "Buccaneers", "Falcons", "Panthers", "Saints",         # N. F. C. South
)
# D1 to D8: the texts SayStand speaks, without the spaces the program puts around them (strings 637 to 777)
DEFAULT_DIVISION_NAMES = (
    "A. F. C. North.", "A. F. C. East.", "A. F. C. West.", "A. F. C. South.",
    "N. F. C. North.", "N. F. C. East.", "N. F. C. West.", "N. F. C. South.",
)


class League:
    def __init__(self, team_names=DEFAULT_TEAM_NAMES, division_names=DEFAULT_DIVISION_NAMES):
        if len(team_names) != TEAM_COUNT or len(division_names) != DIVISIONS:
            raise ValueError("a league has %d teams and %d divisions" % (TEAM_COUNT, DIVISIONS))
        self.team_names = tuple(team_names)
        self.division_names = tuple(division_names)

    @staticmethod
    def _check(division: int, place: int) -> None:
        if not (1 <= division <= DIVISIONS and 1 <= place <= PLACES):
            raise ValueError("no team %r in division %r" % (place, division))

    def team(self, division: int, place: int) -> str:
        """Me.m294(tn1 + tn2 * 9): the nickname of team `place` in `division`."""
        self._check(division, place)
        return self.team_names[(division - 1) * PLACES + (place - 1)]

    def division_text(self, division: int) -> str:
        """The division as SayStand speaks it, with the spaces around it: " A. F. C. North. "."""
        if not 1 <= division <= DIVISIONS:
            raise ValueError("no division %r" % (division,))
        return " " + self.division_names[division - 1] + " "

    def team_id(self, division: int, place: int) -> str:
        """The customization ID of a team: T01 to T32 (division 1 place 1 is T01)."""
        self._check(division, place)
        return "T%02d" % ((division - 1) * PLACES + place)
