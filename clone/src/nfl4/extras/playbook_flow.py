"""The playbooks in a game: the books of the two sides, the computer's weighted choice and the arming of the modifiers (nfl4 only,
rule 0.13; NX5, design 10.4, built in SX.7). This is inspired by Jim Kitchen.

NflRules (extras/nfl_rules.py) owns one `PlaybookFlow` per game and calls it from the hooks:

    resolve(game, state)                  the playbooks of the two sides, once per game (period_clock): the player's from the
                                          F9 settings (Classic, the team's style or a style), the computer's team style
    (the player's menus were SX.7's two-level groups; the catalog's menus replaced them, extras/offense_flow.py in SX.10c and
    extras/defense_flow.py in SX.10d)
    computer_offense / computer_defense   N5.6: the computer's weighted draw over the plays of its style by down, distance,
                                          field position and score (one `below(total)`), the family is the play's
    arm(state, offense_play, defense_play)  before the snap: the H8 modifiers for the two plays that were called
    clear()                               a play withdrawn or a kick-off: nothing is called, no modifier is armed

Classic is never touched: a side whose book is Classic has no menu of plays, no draw and no modifier. Every number is data
(playbook_data.py, the player's styles.txt; tuning.py for the situation percents); this file holds only rules.
"""
from __future__ import annotations

from ..game.gamestate import other
from . import playbook_data as D
from . import playbooks as P
from . import tuning as T
from .franchise.ratings import FranchiseModifiers
from .franchise.staff import game_team_styles
from .qb_runs import to_goal


def team_index(division: int, place: int) -> int:
    """0 to 31: T01 to T32, as league.team_id counts."""
    return (division - 1) * 4 + (place - 1)


class PlaybookFlow:
    def __init__(self, rules):
        self.rules = rules
        # H8: the playbooks' Mod, and (SX.8b, nfl4's Franchise) the ratings' Mod of rosters that carry ratings: the same object as
        # PlaybookModifiers while no roster has any, which is every game that is not a Franchise game
        self.modifiers = FranchiseModifiers()
        self.offense_id = ""                    # the catalog play called for the offense of this play ("O017") or none
        self.defense_id = ""
        # every play that was run: (offense side, offense play ID, defense play ID, offense family, defense family, the kind
        # of the result, its yards): the tests and the calibration count them (a play a penalty took away still counts)
        self.events: list[tuple] = []

    @property
    def table(self) -> P.Table:
        game = self.rules.game
        return getattr(game, "playbook_table", None) or P.DEFAULT_TABLE

    @property
    def rnd(self):
        return self.rules.game.rnd

    # ----- which book each side plays -----

    def resolve(self, game, state) -> None:
        """The playbooks of the game (extras.offense_book and defense_book, one per side, a style key or "classic")."""
        rules, x, table = self.rules, state.extras, self.table
        season = game.season
        teams = game_team_styles(game)                 # SX.8l: in a franchise the coordinators' styles are the teams' (None in every other game)
        if teams is not None:
            table = P.Table(table.names, table.disabled, table.styles, teams)

        def pick(choice: str, team: int, side: str) -> str:
            if choice == D.CLASSIC_KEY:
                return P.CLASSIC
            if choice == D.TEAM_KEY:
                key = table.team_style(team, side)
            else:
                key = choice
            return key if key in table.styles else P.CLASSIC

        own = team_index(season.tn1, season.tn2)
        opponent = team_index(season.tn3, season.tn4)
        computer = rules.playbooks_on
        x.offense_book = [pick(rules.offense_book, own, "O"),
                          pick(D.TEAM_KEY, opponent, "O") if computer else P.CLASSIC]
        x.defense_book = [pick(rules.defense_book, own, "D"),
                          pick(D.TEAM_KEY, opponent, "D") if computer else P.CLASSIC]

    @staticmethod
    def in_use(x) -> bool:
        return any(key != P.CLASSIC for key in x.offense_book + x.defense_book)

    def style(self, state, side: int, role: str) -> str:
        """The style key side `side` plays on offense ("O") or defense ("D"), "classic" when it plays the original's plays."""
        x = state.extras
        books = x.offense_book if role == "O" else x.defense_book
        key = books[side - 1]
        return key if key in self.table.styles else P.CLASSIC

    # ----- the computer's choice (N5.6) -----

    def situation_percent(self, state, family: int) -> int:
        """The percent the situation gives a play of `family` (down, distance, field position and score; design 10.4): 100 is
        no change. The factors are tuning.PB_*, scaled by PB_SITUATION_STRENGTH."""
        x, pct = state.extras, 100
        yards = state.to_go
        if state.down >= 2:                        # first and ten is every drive's start: only the later downs have a distance
            if yards <= T.PB_SHORT_YARDS:
                pct = pct * T.PB_DISTANCE_PERCENT["short"].get(family, 100) // 100
            elif yards >= T.PB_LONG_YARDS:
                pct = pct * T.PB_DISTANCE_PERCENT["long"].get(family, 100) // 100
        if to_goal(state) <= T.PB_RED_ZONE:
            pct = pct * T.PB_RED_ZONE_PERCENT.get(family, 100) // 100
        if state.quarter >= 4 and x.left <= T.PB_LATE_SECONDS:
            lead = state.score(state.wisoff) - state.score(other(state.wisoff))
            if lead <= -T.PB_LATE_MARGIN:
                pct = pct * T.PB_LATE_TRAILING_PERCENT.get(family, 100) // 100
            elif lead >= T.PB_LATE_MARGIN:
                pct = pct * T.PB_LATE_LEADING_PERCENT.get(family, 100) // 100
        return max(1, 100 + (pct - 100) * T.PB_SITUATION_STRENGTH // 100)

    def draw(self, candidates: list[tuple[D.Play, int]]) -> D.Play:
        """One weighted draw: Int(Rnd * total) over the whole weights."""
        total = sum(weight for _play, weight in candidates)
        pick = self.rnd.below(max(1, total))
        for play, weight in candidates:
            if pick < weight:
                return play
            pick -= weight
        return candidates[-1][0]

    def qb_percent(self, state) -> int:
        """The computer's quarterback runs as a percent of Classic's rate: its offense style's (design 7.4)."""
        style = self.style(state, state.wisoff, "O")
        book = self.table.styles.get(style)
        return book.qb_percent if book is not None and style != P.CLASSIC else 100

    def computer_offense(self, state) -> None:
        """After the original's choice and the quarterback runs' draws: the style's play of the family the drawn play has (a
        quarterback run keeps its family) or of the five families by weight and situation. Kicks and tries are left alone."""
        self.offense_id = ""
        x = state.extras
        style = self.style(state, state.wisoff, "O")
        family = state.offense_play
        if style == P.CLASSIC or state.two_point or family in (6, 7):
            return
        usable = self.table.usable(style, "O")
        if family in D.QB_FAMILIES:
            candidates = [(p, w) for p, w in usable if p.family == family]
        else:                                      # on fourth down the original's go-for-it call is a family 1 to 4 (5.7)
            reach = 4 if state.down == 4 else 5
            candidates = [(p, w * self.situation_percent(state, p.family)) for p, w in usable if p.family <= reach]
        if not candidates:
            return
        play = self.draw(candidates)
        self.offense_id, state.offense_play = play.id, play.family

    def computer_defense(self, state) -> None:
        """The computer's defense: the style's play of the family the original's rules chose (repeats are still matched)."""
        self.defense_id = ""
        style = self.style(state, state.defense, "D")
        if style == P.CLASSIC:
            return
        if state.two_point or state.offense_play in (6, 7):      # a try and a kick are the original's, no draw
            return
        candidates = [(p, w) for p, w in self.table.usable(style, "D") if p.family == state.defense_play]
        if candidates:
            self.defense_id = self.draw(candidates).id

    # ----- the snap -----

    def arm(self, state, offense_play: int, defense_play: int) -> None:
        """H8: the rows move by the two plays that were called; nothing called, nothing moves."""
        offense, defense = D.PLAYS.get(self.offense_id), D.PLAYS.get(self.defense_id)
        if (offense is None and defense is None) or state.two_point:
            self.modifiers.arm(None)
            return
        x = state.extras
        if offense is not None and offense.family != offense_play:      # the engine changed the play (a scramble keeps none)
            offense = None
        if defense is not None and defense.family != defense_play:
            defense = None
        mod = P.combined(self.table, x.offense_book[state.wisoff - 1], offense, x.defense_book[state.defense - 1], defense,
                         offense_play, defense_play)
        self.modifiers.arm(mod)

    def record(self, state, outcome) -> None:
        """At the narration end point: what was called (empty for a side that plays Classic) and what came of it."""
        if outcome.offense_play in (0, 6, 7) or state.two_point:     # a kick-off, a field goal, a punt and a try call no play
            return
        self.events.append((outcome.offense, self.offense_id, self.defense_id, outcome.offense_play, outcome.defense_play,
                            outcome.kind, outcome.yards))

    def forget_calls(self) -> None:
        """The play is over: nothing is called. The modifiers stay armed until the ruling of the play was made (the review reads the
        row the play used)."""
        self.offense_id = self.defense_id = ""

    def clear(self) -> None:
        self.forget_calls()
        self.modifiers.arm(None)

    @staticmethod
    def player_uses_a_book(x) -> bool:
        return x.offense_book[0] != P.CLASSIC or x.defense_book[0] != P.CLASSIC
