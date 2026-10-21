"""The catalog's defense in a game: the player's defense menus, the call, the kick defense and the outcome model against the computer's
offense (nfl4 only, rule 0.13; NX-P2 to NX-P8; NFL_PLAYS_DESIGN 2, 4.7 and 7; built in SX.10d, D-094). This is inspired by Jim Kitchen.

NflRules (extras/nfl_rules.py) owns one DefenseFlow per game and calls it from its hooks, as it calls the offense's (extras/offense_flow.py):

    active(state)               the player's defense uses the catalog's menus: the computer has the ball and the player's defense playbook
                                is not Classic (design 2.2: with Classic the original's six calls stay as they are)
    items(state)                H3 defense_menu: the items of the level the player is in (play_menus.PlayMenus, side D), in the original's
                                form: the original's six calls first with their digits, F, A, M, P Kick Defense (fourth down only), O
    action, right, back, key    H3 menu_action, menu_right, menu_back, menu_key: Enter, Right, Left and Backspace, plus and minus
    heading(state)              H3 menu_heading: the name of an open list
    model_play(state)           H19 after the snap sentence: the computer's offense play (its style's catalog play, else the stand-in
                                of its family) against the player's call, through the offense flow's model (`run_model`), so the
                                engine tells it, returns its turnovers and reads its out of bounds as for the player's own plays
    finish(state, outcome)      H2: Again remembers the call, the menu goes to its top

A kick defense call (K031 to K036, design 2.6) is not a play: Enter on it sets the remembered call of the game (extras.kick_defense), says
it (NXB-J22) and the menu goes back to its top. The call the model plays is the call with the personnel matched to the offense's
(extras/plays/personnel.py, Q-P13) and the player's Coverage Shade.
"""
from __future__ import annotations

from ..data import debuglog
from ..game import menus
from ..game.keys import MODIFIER_KEYS
from ..game.rules import MENU_QUIET, MENU_REFRESH
from . import nx_texts as X
from . import playbooks as PB
from .offense_flow import MINUS_CODES, PLUS_CODES, engine_family
from .plays import catalog as C
from .plays import personnel
from .plays import play_menus as PM
from .qb_runs import to_goal

PREFIX = "pd:"                      # the action of an item of the defense's menus: ("pd:call", "D017")
# the stand-in play of each of the computer's offense families when its offense has no style play of the catalog (Line Plunge, End Run,
# Screen Pass, Short Pass, Long Pass, the quarterback's sneak, keeper and draw): the usual play of the family's first list, no draw
STAND_INS = {1: "O001", 2: "O010", 3: "O017", 4: "O025", 5: "O032", 8: "O046", 9: "O047", 10: "O048"}
KICK_DEFENSE_IDS = ("K031", "K032", "K033", "K034", "K035", "K036")


class DefenseFlow:
    def __init__(self, rules):
        self.rules = rules
        self.menus = PM.PlayMenus(PM.Context("D"))
        self.called = ""                   # the defense call the player made for this play ("D017"), "" none
        # every play the model played against the player's call: (the computer's play, the call, the result kind, the yards, the call's
        # defensive backs and box as played): the tests and the calibration count them
        self.events: list[tuple] = []

    @property
    def game(self):
        return self.rules.game

    @property
    def table(self) -> PB.Table:
        return getattr(self.game, "playbook_table", None) or PB.DEFAULT_TABLE

    @property
    def favourites(self) -> tuple:
        return self.rules.offense.favourites[1]

    def resolve(self, game, state) -> None:
        self.reset()

    # ----- which menus -----

    def active(self, state) -> bool:
        x = state.extras
        return state.wisoff == 2 and x is not None and x.defense_book[0] != PB.CLASSIC and not state.two_point

    def reset(self) -> None:
        self.menus.reset()

    def clear(self) -> None:
        self.called = ""

    # ----- the context and the items -----

    def usable(self, state) -> frozenset:
        """The defense calls and the kick defense calls the player may make: on in plays.txt."""
        disabled = self.table.disabled
        return frozenset(c.id for c in C.CATALOG if (c.side == "D" or c.id in KICK_DEFENSE_IDS) and c.id not in disabled)

    def context(self, state) -> PM.Context:
        x = state.extras
        usable = self.usable(state)
        last = x.again[1] if x.again[1] in usable else ""
        favourites = tuple(i for i in self.favourites if i in usable)
        return PM.Context("D", False, x.qb_on, False, False, state.down == 4, last, favourites, usable)

    def items(self, state) -> list[menus.MenuItem]:
        self.menus.set_context(self.context(state))
        out = []
        for n, item in enumerate(self.menus.items(), start=1):
            action = (PREFIX + item.action[0], item.action[1])
            out.append(menus.MenuItem(" %d. %s " % (n, self.item_text(state, item)), item.digit, action, item.letter))
        return out

    def item_text(self, state, item: PM.Item) -> str:
        return self.rules.offense.item_text(state, item)

    def heading(self, state) -> str:
        return self.rules.offense.heading_of(self.menus)

    # ----- the keys -----

    @staticmethod
    def owns(action) -> bool:
        return isinstance(action[0], str) and action[0].startswith(PREFIX)

    @staticmethod
    def item_of(action) -> PM.Item:
        return PM.Item("", -1, "", (action[0][len(PREFIX):], action[1]))

    def action(self, state, action):
        """Enter on an item: (PLAY, family) a call is made; True the level changed or the kick defense was set; MENU_REFRESH a setting
        changed; False nothing happens."""
        done = self.menus.enter(self.item_of(action))
        if done is True or done is False:
            return done
        kind, value = done
        if kind == PM.CALL and value in KICK_DEFENSE_IDS:
            self.rules.kicks.set_kick_defense(state, value)
            self.reset()
            return True
        if kind == PM.CALL:
            return self.call(state, value)
        if kind == PM.PICK:
            pick = self.pick(state, value)
            if not pick:                    # every call of the family is off in plays.txt: the original's call, as SX.7 did
                self.clear()
                self.reset()
                return (menus.PLAY, value)
            self.game.say5(X.text("NXB-H15", name=self.table.name(pick)))
            return self.call(state, pick)
        if kind == PM.SETTING:
            self.rules.offense.change_setting(state, value)
            return MENU_REFRESH
        if kind == PM.FIND:
            return self.find(state)
        return False

    def call(self, state, play_id: str):
        concept = C.BY_ID[play_id]
        self.called = play_id
        self.reset()
        debuglog.event("extras", "catalog_call", play=play_id, name=concept.name, down=state.down, to_go=state.to_go)
        return (menus.PLAY, concept.family)

    def pick(self, state, family: int) -> str:
        """Enter on one of the original's six calls (design 2.2, SX.10e): the playbook's pick, the computer's calling weights over the
        family's usable calls for the player's style and the offense's situation (one draw); the first usable call of the family's lists
        when none has a weight (no draw); "" when every call of the family is off."""
        context = self.context(state)
        family_calls = [c for group in PM.family_groups("D", family) for c in PM.concepts_of(group, context) if c.side == "D"]
        if not family_calls:
            return ""
        picked = self.rules.books.pick(state, 1, "D", family_calls)
        return picked or family_calls[0].id

    def find(self, state):
        self.menus.set_context(self.context(state))
        typed = self.game.getter(X.text(PM.TEXT["find_prompt"]))
        if self.menus.search(typed):
            return True
        self.game.say5(X.text(PM.TEXT["no_match"]))
        return False

    def right(self, state, item) -> bool:
        if not self.owns(item.action):
            return False
        self.menus.set_context(self.context(state))
        return self.menus.right(self.item_of(item.action))

    def back(self, state) -> bool:
        return self.menus.back()

    def key(self, state, code: str, item):
        """Plus and minus on a call: the defense's favourites (favourites.txt, its second half), written at once."""
        if code.isdigit() and int(code) in MODIFIER_KEYS:
            return MENU_QUIET
        if code not in PLUS_CODES + MINUS_CODES or item is None or not self.owns(item.action):
            return False
        kind, value = item.action[0][len(PREFIX):], item.action[1]
        if kind not in (PM.CALL, PM.AGAIN) or value not in C.BY_ID or C.BY_ID[value].side != "D":
            return False
        flow = self.rules.offense
        offense, defense = flow.favourites
        if code in PLUS_CODES:
            defense, text_id = PM.add_favourite(defense, value)
        else:
            defense, text_id = PM.remove_favourite(defense, value)
        flow.favourites = (offense, defense)
        flow.save_favourites()
        self.game.say5(X.text(text_id))
        debuglog.event("extras", "favourite", play=value, added=code in PLUS_CODES, count=len(defense))
        return MENU_REFRESH

    def describe_row(self, action) -> str | None:
        return self.menus.describe(self.item_of(action)) or None

    # ----- the play -----

    def offense_concept(self, state) -> C.Concept:
        """The computer's offense play the model plays: its style's play of the catalog (SX.7's O001 to O052 are the catalog's), else the
        stand-in of the family it chose (no draw)."""
        concept = C.BY_ID.get(self.rules.books.offense_id)
        if concept is None or concept.side != "O" or engine_family(concept) != state.offense_play:
            concept = C.BY_ID[STAND_INS.get(state.offense_play, STAND_INS[1])]
        return concept

    def model_play(self, state):
        """After the snap sentence: the result of the computer's play against the player's call, or None (no call of the catalog, or a
        play the model does not play: the original's tables)."""
        call = C.BY_ID.get(self.called) if state.wisoff == 2 else None
        if call is None or call.side != "D" or state.two_point or state.offense_play not in STAND_INS:
            return None
        concept = self.offense_concept(state)
        settings = state.extras.play_settings
        played = personnel.adjust(call.params, concept.personnel, to_goal(state), settings.get("defense_personnel", personnel.MATCH),
                                  settings.get("coverage_shade", personnel.BOOK))
        result = self.rules.offense.run_model(state, concept, call.id, played)
        self.events.append((concept.id, call.id, result.kind, result.yards, played.backs, played.box))
        return result

    def finish(self, state, outcome) -> None:
        """The narration end point (H2): Again remembers the player's call, the menu is at its top for the next play."""
        if self.called and outcome.offense == 2 and outcome.offense_play not in (0, 6, 7):
            state.extras.again[1] = self.called
        self.called = ""
        self.reset()


__all__ = ["DefenseFlow", "STAND_INS"]
