"""The playbooks in a game: the books of the two sides, the computer's weighted choice and the arming of the modifiers (nfl4 only,
rule 0.13; NX5, design 10.4, built in SX.7). This is inspired by Jim Kitchen.

NflRules (extras/nfl_rules.py) owns one `PlaybookFlow` per game and calls it from the hooks:

    resolve(game, state)                  the playbooks of the two sides, once per game (period_clock): the player's from the
                                          F9 settings (Classic, the team's style or a style), the computer's team style
    (the player's menus were SX.7's two-level groups; the catalog's menus replaced them, extras/offense_flow.py in SX.10c and
    extras/defense_flow.py in SX.10d)
    computer_offense / computer_defense   N5.6: the computer's weighted draw over the plays of its style by down, distance,
                                          field position and score (one `below(total)`), the family is the play's. SX.10e (D-095):
                                          in a game that plays the catalog (the player uses a playbook, kick_flow.kicks_on) a side with
                                          a style calls over the WHOLE catalog (extras/plays/calling.py: the style's lean, the data's
                                          mix by down and distance, the defense's coverage, rusher and box shares, trick plays rare,
                                          kneel, spike, the Hail Mary, the try); the model plays the call (H19, offense_flow.computer_play)
    pick(state, side, role, family)       the playbook's pick behind Enter on a family of the player's catalog menus (the same weights)
    arm(state, offense_play, defense_play)  before the snap: the H8 modifiers for the two plays that were called
    clear()                               a play withdrawn or a kick-off: nothing is called, no modifier is armed

Classic is never touched: a side whose book is Classic has no menu of plays, no draw and no modifier. Every number is data
(playbook_data.py, the player's styles.txt; tuning.py for the situation percents); this file holds only rules.
"""
from __future__ import annotations

from ..data import debuglog
from ..game.gamestate import other
from . import playbook_data as D
from . import playbooks as P
from . import tuning as T
from .franchise.ratings import FranchiseModifiers
from .franchise.staff import game_team_styles
from .kick_flow import kicks_on
from .offense_flow import engine_family
from .plays import calling as K
from .plays import catalog as C
from .qb_runs import to_goal


def team_index(division: int, place: int) -> int:
    """0 to 31: T01 to T32, as league.team_id counts."""
    return (division - 1) * 4 + (place - 1)


BLITZ_FAMILY = 4          # the original's defense family 4, Blitz
BLITZ_MIN_RUSHERS = 5


def blitz_family_sends_five(candidates):
    """Enter on the Blitz item (a tester, 2026-10-23: "blitzes rarely get home"): the draw is among the calls of the family that send five or
    more; a list of the family's plays that holds only four-man looks (one play chosen by name) is left as it is."""
    calls = list(candidates)
    if not calls or any(getattr(c, "family", 0) != BLITZ_FAMILY or c.side != "D" for c in calls):
        return calls
    sending = [c for c in calls if c.params.rushers >= BLITZ_MIN_RUSHERS]
    return sending or calls


class PlaybookFlow:
    def __init__(self, rules):
        self.rules = rules
        # H8: the playbooks' Mod, and (SX.8b, nfl4's Franchise) the ratings' Mod of rosters that carry ratings: the same object as
        # PlaybookModifiers while no roster has any, which is every game that is not a Franchise game
        self.modifiers = FranchiseModifiers()
        self.offense_id = ""                    # the catalog play called for the offense of this play ("O017") or none
        self.defense_id = ""
        self.catalog = False                    # SX.10e: offense_id is the computer's call over the whole catalog: the model plays it
        # SX.10e: every call the computer made over the catalog: (side, "O" or "D", the play, down, to go, yards to the goal, quarter):
        # the tests and the calibration count them
        self.calls: list[tuple] = []
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

    # ----- SX.10e: the calling over the whole catalog (extras/plays/calling.py, D-095) -----

    def catalog_side(self, state, side: int, role: str) -> bool:
        """Side `side` calls over the catalog in this game: the game plays the catalog (the player uses a playbook) and the side's book
        for `role` is a style."""
        return kicks_on(state.extras) and self.style(state, side, role) != P.CLASSIC

    def own_plays(self, style: str, role: str) -> frozenset:
        """A style's own SX.7 plays (playbook_data), which count double in its calling."""
        book = D.STYLE_BY_KEY.get(style)
        if book is None:
            return frozenset()
        return frozenset(i for i, _w in (book.offense if role == "O" else book.defense))

    def call_situation(self, state, last_play: bool = False) -> K.Situation:
        x = state.extras
        return K.Situation(state.down, state.to_go, to_goal(state), state.quarter, x.left,
                           state.score(state.wisoff) - state.score(other(state.wisoff)), bool(state.two_point), last_play)

    def usable_ids(self, role: str) -> frozenset:
        disabled = self.table.disabled
        side = "O" if role == "O" else "D"
        return frozenset(c.id for c in C.CATALOG if c.side == side and c.id not in disabled)

    def weights(self, state, side: int, role: str, candidates) -> list[tuple[str, int]]:
        """The calling's weights over `candidates` for the side's style and the situation (extras/plays/calling.py): no draw, no state."""
        style = self.style(state, side, role)
        own = self.own_plays(style, role)
        sit = self.call_situation(state)
        if role != "O":
            candidates = blitz_family_sends_five(candidates)
        return (K.offense_weights(candidates, style, own, sit) if role == "O"
                else K.defense_weights(candidates, style, own, sit))

    def pick(self, state, side: int, role: str, candidates) -> str:
        """The playbook's pick behind Enter on a family of the player's catalog menus (design 2.2): the calling's weights over the family's
        usable plays for the side's style and the situation, one draw; "" when none has a weight (the caller takes the first play)."""
        return K.draw(self.weights(state, side, role, candidates), self.rnd)

    def likely(self, state, side: int, role: str, candidates) -> tuple[tuple[str, ...], int]:
        """The W key (D-112, Q-050): the play or plays `pick` would most likely return from `candidates` (all that share the greatest weight,
        in the order of `candidates`) and the chance of each in whole percent (1 to 100), from the same weights and with NO draw, so asking
        changes nothing in the game. Many plays share a weight (a list of equal plays), and the key must not name one of them as the
        favourite. No weight at all (the playbook never calls these plays, as the kinds of kicks): the first play, as `pick`'s callers take
        it, with 0 percent; ((), 0) with no candidates."""
        if not candidates:
            return (), 0
        weights = self.weights(state, side, role, candidates)
        total = sum(w for _i, w in weights)
        if total <= 0:
            return (candidates[0].id,), 0
        top = max(w for _i, w in weights)
        return tuple(i for i, w in weights if w == top), max(1, min(100, (top * 100 + total // 2) // total))

    def catalog_offense(self, state) -> None:
        """The computer's call over the catalog, after the original's rules chose the kind of play (a scrimmage play, the field goal or the
        punt on fourth down or the last play): the try's play, a kneel, a spike, the Hail Mary or the laterals on the last play, or one
        draw over the whole catalog by the style and the situation. The engine's play number becomes the call's family."""
        x = state.extras
        side, family = state.wisoff, state.offense_play
        style = self.style(state, side, "O")
        usable = self.usable_ids("O") | ({"K026"} if "K026" not in self.table.disabled else frozenset())
        lead = state.score(side) - state.score(other(side))
        their = x.timeouts_of(other(side)) if x.timeouts_on else 0
        own = x.timeouts_of(side) if x.timeouts_on else 0
        clock = self.rules.clock
        last = clock is not None and clock.is_last_play()
        call = ""
        if state.two_point:
            call = K.draw(K.try_weights(usable), self.rnd)
        elif K.kneel_helps(state.quarter, x.left, state.down, lead, their) and (
                state.quarter == 4 or (x.left <= K.COMPUTER_KNEEL_HALF[0] and to_goal(state) >= K.COMPUTER_KNEEL_HALF[1])):
            call = K.KNEEL if K.KNEEL in usable else ""
        elif family in (6, 7):
            if last:
                call = K.last_play_call(state.quarter, lead, to_goal(state), family == 6)
                call = call if call in usable else ""
        elif (K.spike_wanted(state.quarter, x.left, x.running, state.down, lead, own, to_goal(state)) and K.SPIKE in usable
              and self.rnd(K.SPIKE_CHANCE) == 1):
            call = K.SPIKE
        else:
            candidates = [c for c in C.OFFENSE if c.id in usable and (x.qb_on or c.kind not in ("sneak", "qb_run"))]
            call = K.draw(K.offense_weights(candidates, style, self.own_plays(style, "O"), self.call_situation(state),
                                            self.qb_percent(state)), self.rnd)
        if not call:
            return
        concept = C.BY_ID[call]
        self.offense_id, self.catalog = call, True
        state.offense_play = engine_family(concept)
        self.note(state, side, "O", call)

    def catalog_defense(self, state) -> None:
        """The computer's defense call over the catalog against a play the model plays: one draw over every usable call by the style and
        the offense's situation (the try's calls on a try, the goal line calls near the goal, prevent to keep a late lead, the Hail Mary
        defense against a last play from far away)."""
        side = state.defense
        style = self.style(state, side, "D")
        clock = self.rules.clock
        last = clock is not None and clock.is_last_play()
        usable = self.usable_ids("D")
        candidates = [c for c in C.DEFENSE if c.id in usable]
        call = K.draw(K.defense_weights(candidates, style, self.own_plays(style, "D"), self.call_situation(state, last)), self.rnd)
        if call:
            self.defense_id = call
            self.note(state, side, "D", call)

    def note(self, state, side: int, role: str, call: str) -> None:
        self.calls.append((side, role, call, state.down, state.to_go, to_goal(state), state.quarter))
        debuglog.event("extras", "computer_call", side=side, role=role, play=call, down=state.down, to_go=state.to_go,
                       to_goal=to_goal(state))

    def model_plays(self, state) -> bool:
        """The play to come is one the model plays: the player's own catalog call or the computer's."""
        if self.catalog:
            return True
        offense = self.rules.offense
        return state.wisoff == 1 and offense.called in C.BY_ID

    # ----- SX.7's draw over a style's own plays (a game that does not play the catalog) -----

    def computer_offense(self, state) -> None:
        """After the original's choice and the quarterback runs' draws: the style's play of the family the drawn play has (a
        quarterback run keeps its family) or of the five families by weight and situation. Kicks and tries are left alone.
        SX.10e: a side that calls over the catalog calls there (catalog_offense)."""
        self.offense_id = ""
        self.catalog = False
        x = state.extras
        style = self.style(state, state.wisoff, "O")
        family = state.offense_play
        if self.catalog_side(state, state.wisoff, "O"):
            self.catalog_offense(state)
            return
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
        if state.offense_play not in (6, 7) and self.catalog_side(state, state.defense, "D") and self.model_plays(state):
            self.catalog_defense(state)                          # SX.10e: the call over the catalog against a model play
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
        if self.model_plays(state):                # SX.10e: the outcome models play it; SX.7's table rows have nothing to move
            offense = defense = None
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
        self.catalog = False

    def clear(self) -> None:
        self.forget_calls()
        self.modifiers.arm(None)

    @staticmethod
    def player_uses_a_book(x) -> bool:
        return x.offense_book[0] != P.CLASSIC or x.defense_book[0] != P.CLASSIC
