"""The catalog's offense in a game: the player's play menus, the call, the outcome model and the turnover's return (nfl4 only, rule 0.13;
NX-P2 to NX-P8 and NX-R7 (G26-8, G26-9, G26-12), NFL_PLAYS_DESIGN 2 and 7; built in SX.10c, D-093). This is inspired by Jim Kitchen.

NflRules (extras/nfl_rules.py) owns one OffenseFlow per game and calls it from its hooks:

    active(state)               the player's offense uses the catalog's menus: the player has the ball and his offense playbook is not
                                Classic (a style or the team's; design 2.2: with Classic the original's items stay as they are)
    items(state)                H3 offense_menu: the items of the level the player is in (play_menus.PlayMenus), in the original's form
    action, right, back, key    H3 menu_action, menu_right, menu_back, menu_key: Enter, Right, Left and Backspace, plus and minus, Shift
    heading(state)              H3 menu_heading: the name of an open list
    model_play(state)           H19 after the snap sentence: the called play's result from extras/plays/model.py; the engine tells it
                                with the original's sentence pools (game/pag_catalog.py)
    turnover_return(state)      H19 the spot of an interception or a lost fumble of that play, or its touchdown (G26-8)
    finish(state, outcome)      H2 at the narration end point: the record names the play, Again remembers it, the menu goes to its top

The playbook's pick behind Enter on a family (design 2.2, SX.10e) is the computer's calling weights over that family's plays
(extras/plays/calling.py through PlaybookFlow.pick). The defense call the model plays against is the computer's call over the whole
catalog (SX.10e, PlaybookFlow.catalog_defense) or, with no style, the stand-in call of its family (DEFAULT_CALLS), with no draw; its
personnel is matched to the player's (SX.10d, extras/plays/personnel.py, Q-P13). `computer_play` (SX.10e) plays the computer's own call
over the catalog against the other side's call, so two computer sides (the calibration) play the catalog too.
SX.10d: Right on Field Goal and Punt opens their kinds and fakes (the punts K011 to K016, the fake field goals K022 and K023); calling one
gives the engine the original's Field Goal or Punt and the kick flow (extras/kick_flow.py) reads the call; the try's list offers the
swinging gate (K026), played here as a run of the end that works when the fake kick's model says so. `run_model` plays any offense play
against any call and is the defense flow's too (extras/defense_flow.py: the computer's offense against the player's call).
"""
from __future__ import annotations

import logging

from ..data import debuglog
from ..game import menus
from ..game.gamestate import other, own_half
from ..game.keys import MODIFIER_KEYS
from ..game.rules import MENU_QUIET, MENU_REFRESH
from . import nx_texts as X
from . import playbooks as PB
from . import tuning as T
from .plays import calling as K
from .plays import catalog as C
from .plays import favourites as F
from .plays import model as M
from .plays import model_data as MD
from .plays import personnel
from .plays import play_menus as PM
from .qb_runs import to_goal

log = logging.getLogger("nfl4.extras")

KEY_PLUS_PAD, KEY_PLUS_MAIN, KEY_MINUS_PAD, KEY_MINUS_MAIN = "107", "187", "109", "189"
PLUS_CODES, MINUS_CODES = (KEY_PLUS_PAD, KEY_PLUS_MAIN), (KEY_MINUS_PAD, KEY_MINUS_MAIN)
PREFIX = "pm:"                      # the action of an item of the catalog's menus: ("pm:call", "O027")
# the stand-in call of each of the original's six defense families when the computer's defense has no style (Goal Line, Short Run, Long
# Run, Blitz, Short Pass, Long Pass): the most usual call of the family's first list
DEFAULT_CALLS = {1: "D002", 2: "D004", 3: "D007", 4: "D014", 5: "D017", 6: "D022"}
QB_FAMILY = {"sneak": 8, "keeper": 9, "draw": 10}            # playtables QB_SNEAK, QB_KEEPER, QB_DRAW
QB_KIND_KEYS = {"O048": "draw"}                              # the designed quarterback runs that are told as a draw; a sneak is a sneak
QB_PLAYS = {8: "O046", 9: "O047", 10: "O048"}                # the offense items 8, 9 and 0 (descriptions.QB_PLAYS)
PASS_KINDS = ("pass", "screen", "play_action", "boot", "trick_pass", "max_protect", "hail_mary")
OWN_FORMATION_PLAYS = ("O141", "O152", "O153")     # SX.13: the Formation setting never changes these (the throwback, the kneel, the spike)
RUN_KINDS = ("run", "draw", "trick_run", "laterals")
SETTING_BOOK = "book"               # a setting's "the playbook's choice": the concept's own formation, personnel, motion, side
KICK_FAMILIES = {"kg02": 7, "kg03": 6}       # SX.10d: the kinds of punt and the fakes are the original's Punt, the fake field goals its Field Goal
GATE = "K026"                       # the swinging gate try (design 2.6, Q-P5)


def engine_family(concept: C.Concept) -> int:
    """The original's offense play number the engine uses for the call before the snap (the computer's defense draw, its match of a
    repeated call, the snap's route): the concept's family, a quarterback run's 8 to 10, or the family its kind is like."""
    if concept.id == GATE:
        return 2                                            # the swinging gate: a run of the end (it is listed with the field goals)
    if concept.side == "K":
        return KICK_FAMILIES.get(concept.group, 2)
    if concept.kind in ("sneak", "qb_run"):
        return QB_FAMILY[qb_key(concept)]
    if concept.kind == "kneel":
        return 1
    if concept.kind == "spike":
        return 4
    if 1 <= concept.family <= 5:
        return concept.family
    if concept.kind in RUN_KINDS:
        return 2 if concept.params and concept.params[0] in ("end",) or concept.kind == "laterals" else 1
    if concept.kind == "option":
        return 2 if concept.params[2] else 1
    if concept.kind == "rpo":
        return 1
    if concept.kind == "screen":
        return 3
    if concept.kind == "hail_mary":
        return 5
    return 4


def qb_key(concept: C.Concept) -> str:
    if concept.kind == "sneak":
        return "sneak"
    return QB_KIND_KEYS.get(concept.id, "keeper")


def narration_family(concept: C.Concept, result: M.Result) -> int:
    """The engine's play number while the result is told: a run's 1 (inside) or 2 (an end run), a pass's 3 (a screen), 4 or 5 (thrown 15
    yards or more), a quarterback run's 8 to 10. It decides the original's sentences, the tackle sound and the end of the play (game/pag.py
    `ran`)."""
    if result.kind == "kneel":
        return 1
    if result.kind == "spike":
        return 4
    if result.gap == "qb":
        return QB_FAMILY["keeper" if result.branch == "keep" else result.branch]
    if result.gap:
        return 2 if result.gap in ("end", "laterals") else 1
    if concept.kind == "screen" or (result.route == "screen"):
        return 3
    if result.band >= MD.DEEP_IN or concept.kind == "hail_mary":
        return 5
    if result.band < 0 and engine_family(concept) in (3, 5):
        return engine_family(concept)
    return 4


class OffenseFlow:
    def __init__(self, rules):
        self.rules = rules
        self.menus = PM.PlayMenus(PM.Context())
        self.called = ""                   # the concept the player called for this play ("O027"), "" none
        self.result: M.Result | None = None     # the model's result of the play being told (its out of bounds, its turnover's return)
        self.favourites: tuple[tuple, tuple] = ((), ())
        self.played = ""                   # the offense play the model played this play (the player's, or the computer's against the
        #                                    player's defense call, SX.10d); "" none
        self.events: list[tuple] = []      # (concept, call, result kind, yards, branch): the tests and the calibration count them

    @property
    def game(self):
        return self.rules.game

    @property
    def table(self) -> PB.Table:
        return getattr(self.game, "playbook_table", None) or PB.DEFAULT_TABLE

    def resolve(self, game, state) -> None:
        """Once per game (H1): the favourites of the player's file, the menu at its top."""
        favourites = getattr(game, "favourite_plays", None)
        self.favourites = (tuple(favourites[0]), tuple(favourites[1])) if favourites else ((), ())
        self.reset()

    # ----- which menus -----

    def active(self, state) -> bool:
        x = state.extras
        return state.wisoff == 1 and x is not None and x.offense_book[0] != PB.CLASSIC

    def reset(self) -> None:
        """A play is over or a timeout was called: the menu starts at its top (design 2.5)."""
        self.menus.reset()

    def clear(self) -> None:
        """Nothing is called (a play withdrawn by a timeout, a foul before the snap, a kick-off)."""
        self.called = self.played = ""
        self.result = None

    # ----- the context and the items -----

    def usable(self, state) -> frozenset:
        """The offense concepts the player may call: on in plays.txt, and the quarterback's runs only while that switch is on; the kinds of
        punt, the fakes and the swinging gate with the kicks of 2026 (SX.10d)."""
        disabled = self.table.disabled
        x = state.extras
        qb_on = x.qb_on
        plays = {c.id for c in C.OFFENSE if c.id not in disabled and (qb_on or c.kind not in ("sneak", "qb_run"))}
        if self.rules.kicks.on(state):
            plays |= {c.id for c in C.KICKS if (c.group in KICK_FAMILIES or c.id == GATE) and c.id not in disabled}
        return frozenset(plays)

    def context(self, state) -> PM.Context:
        x = state.extras
        usable = self.usable(state)
        last = x.again[0] if x.again[0] in usable else ""
        favourites = tuple(i for i in self.favourites[0] if i in usable)
        return PM.Context("O", bool(state.two_point), x.qb_on, self.kneel_helps(state), self.spike_helps(state), False, last,
                          favourites, usable)

    @staticmethod
    def kneel_helps(state) -> bool:
        """Design 2.7: the offense leads in the fourth quarter and kneels can run the clock out (the time left at most the downs left times
        40 seconds, less 40 for each timeout the defense has), or the first half is in its last seconds (the rule is calling.kneel_helps,
        which the computer's calling reads too, SX.10e)."""
        x = state.extras
        theirs = x.timeouts_of(2) if x.timeouts_on else 0
        return K.kneel_helps(state.quarter, x.left, state.down, state.score(1) - state.score(2), theirs, bool(state.two_point))

    @staticmethod
    def spike_helps(state) -> bool:
        """Design 2.7: the clock runs in the last two minutes of a half and a down is left after the spike."""
        x = state.extras
        return (not state.two_point and state.quarter in (2, 4) and x.running and 0 < x.left <= 120 and state.down < 4)

    def items(self, state) -> list[menus.MenuItem]:
        self.menus.set_context(self.context(state))
        out = []
        for n, item in enumerate(self.menus.items(), start=1):
            action = (PREFIX + item.action[0], item.action[1])
            out.append(menus.MenuItem(" %d. %s " % (n, self.item_text(state, item)), item.digit, action, item.letter))
        return out

    def name(self, play_id: str) -> str:
        return self.table.name(play_id)

    def item_text(self, state, item: PM.Item) -> str:
        kind, value = item.action
        if item.text_id.startswith("="):
            return item.text_id[1:]
        if kind == PM.CALL:
            return self.name(value)
        if kind == PM.AGAIN:
            return "%s, %s" % (X.text(item.text_id).strip(), self.name(value))
        if kind == PM.SETTING:
            current = state.extras.play_settings.get(value, C.SETTINGS[value][0])
            return "%s, %s" % (X.text(item.text_id).strip(), X.text(PM.SETTING_VALUE_TEXT[(value, current)]).strip())
        return X.text(item.text_id).strip()

    def heading(self, state) -> str:
        """The name of the open list, said in place of the coach's prompt (design 2.3); "" at the top."""
        return self.heading_of(self.menus)

    @staticmethod
    def heading_of(menus_: PM.PlayMenus) -> str:
        """The heading of either side's menus (the defense flow's too)."""
        if menus_.level == PM.TOP:
            return ""
        if menus_.level == PM.LIST:
            text_id, n, m = menus_.heading()
            name = X.text(text_id).strip()
            return X.text("NXB-H13", list=name, n=n, m=m) if n else X.text("NXB-H14", list=name)
        word = {PM.MORE_LEVEL: PM.TEXT[PM.MORE], PM.FAV_LEVEL: PM.TEXT[PM.FAVOURITES], PM.FOUND: PM.TEXT[PM.FIND],
                PM.SETTINGS_LEVEL: PM.TEXT[PM.SETTINGS]}[menus_.level]
        return X.text("NXB-H14", list=X.text(word).strip())

    # ----- the keys -----

    @staticmethod
    def owns(action) -> bool:
        return isinstance(action[0], str) and action[0].startswith(PREFIX)

    @staticmethod
    def item_of(action) -> PM.Item:
        return PM.Item("", -1, "", (action[0][len(PREFIX):], action[1]))

    def action(self, state, action):
        """Enter on an item: (PLAY, family) a play is chosen; True the level changed (the menu from its top); MENU_REFRESH a setting
        changed; False nothing happens (the menu stays)."""
        done = self.menus.enter(self.item_of(action))
        if done is True or done is False:
            return done
        kind, value = done
        if kind == PM.CALL:
            return self.call(state, value)
        if kind == PM.PICK:
            pick = self.pick(state, value)
            if not pick:                    # SX.10d: every play of the family is off in plays.txt: the original's play, as SX.7 did
                self.clear()
                self.reset()
                return (menus.PLAY, value)
            self.game.say5(X.text("NXB-H15", name=self.name(pick)))
            return self.call(state, pick)
        if kind == PM.KICK:                 # the original's Field Goal and Punt (the kick flow plays its usual kind, SX.10d)
            self.clear()
            self.reset()
            return (menus.PLAY, value)
        if kind == PM.SETTING:
            self.change_setting(state, value)
            return MENU_REFRESH
        if kind == PM.FIND:
            return self.find(state)
        return False

    def call(self, state, play_id: str):
        concept = C.BY_ID[play_id]
        self.called = play_id
        self.result = None
        self.reset()
        debuglog.event("extras", "catalog_call", play=play_id, name=concept.name, down=state.down, to_go=state.to_go)
        return (menus.PLAY, engine_family(concept))

    def pick(self, state, family: int) -> str:
        """Enter on a family (design 2.2, SX.10e): the playbook's pick, the computer's calling weights (extras/plays/calling.py) over the
        family's usable plays for the player's style, down, distance, field and score (one draw); the first usable play of the family's
        first list when none has a weight (no draw); "" when every play of the family is off."""
        usable = self.usable(state)
        if family in QB_PLAYS and QB_PLAYS[family] in usable:
            return QB_PLAYS[family]
        family_plays = self.family_plays(state, family)
        if not family_plays:
            return ""                       # every play of the family is off (SX.10d: the original's play, not an off play)
        picked = self.rules.books.pick(state, 1, "O", family_plays)
        return picked or family_plays[0].id

    def family_plays(self, state, family: int) -> list[C.Concept]:
        """The usable plays of the lists Right opens from one of the original's play types, in the order of the lists."""
        context = self.context(state)
        return [c for group in PM.family_groups("O", family) for c in PM.concepts_of(group, context)]

    def likely_text(self, state, item) -> str:
        """The W key (D-112, Q-050): what the playbook would most likely pick for the play type the menu is on, or most likely call in the
        list it is in, and how often (the same weights as `pick`, no draw); one play (a quarterback run, a kneel, the original's Field Goal
        and Punt, a play of a list of favourites) says it is one play. "" for an item that is none of these (the caller says what W is for)."""
        kind, value = item.action[0][len(PREFIX):], item.action[1]
        return likely_for(self, state, "O", kind, value, lambda family: self.family_plays(state, family),
                          PM.offense_family_items(), QB_PLAYS)

    def change_setting(self, state, name: str) -> None:
        """Enter on a setting of Formation and Tempo: its next value (the values go around); kept with the game (extras.play_settings)."""
        values = C.SETTINGS[name]
        settings = state.extras.play_settings
        now = settings.get(name, values[0])
        new = values[(values.index(now) + 1) % len(values)] if now in values else values[0]
        if new == values[0]:
            settings.pop(name, None)
        else:
            settings[name] = new
        debuglog.event("setting", "play_setting", name=name, value=new)

    def find(self, state):
        """Find a Play by Name (design 2.5): the typed box (the only place in a game where T is a letter, rule 0.22)."""
        self.menus.set_context(self.context(state))
        typed = self.game.getter(X.text(PM.TEXT["find_prompt"]))
        if self.menus.search(typed):
            return True
        self.game.say5(X.text(PM.TEXT["no_match"]))
        return False

    def right(self, state, item) -> bool:
        """Right: a family's lists; on Field Goal and Punt their kinds and fakes, with the kicks of 2026 (SX.10d)."""
        if not self.owns(item.action) or (item.action[0] == PREFIX + PM.KICK and not self.rules.kicks.on(state)):
            return False
        self.menus.set_context(self.context(state))
        return self.menus.right(self.item_of(item.action))

    def back(self, state) -> bool:
        return self.menus.back()

    def key(self, state, code: str, item):
        """Plus and minus on a play add it to the favourites or take it off (design 2.5), written to favourites.txt at once; a lone Shift
        (the plus key of the main row needs it) is nothing."""
        if code.isdigit() and int(code) in MODIFIER_KEYS:
            return MENU_QUIET
        if code not in PLUS_CODES + MINUS_CODES or item is None or not self.owns(item.action):
            return False
        kind, value = item.action[0][len(PREFIX):], item.action[1]
        if kind not in (PM.CALL, PM.AGAIN) or value not in C.BY_ID:
            return False
        offense, defense = self.favourites
        if code in PLUS_CODES:
            offense, text_id = PM.add_favourite(offense, value)
        else:
            offense, text_id = PM.remove_favourite(offense, value)
        self.favourites = (offense, defense)
        self.save_favourites()
        self.game.say5(X.text(text_id))
        debuglog.event("extras", "favourite", play=value, added=code in PLUS_CODES, count=len(offense))
        return MENU_REFRESH

    def save_favourites(self) -> None:
        """favourites.txt written whole (the Customize folder of the program); the game's copy follows. A rig without the folder keeps them
        in memory only; a file that cannot be written is said in the log and the game goes on."""
        game = self.game
        game.favourite_plays = self.favourites
        custom = getattr(game, "customization", None)
        if custom is None:
            return
        if not F.write(custom.folder, *self.favourites):
            log.warning("favourites.txt could not be written; the favourites stay for this run")

    def describe_row(self, action) -> str | None:
        """The D key (NX-P8): the row of the item's plain description, through the menus' own `describe`."""
        return self.menus.describe(self.item_of(action)) or None

    # ----- the play -----

    def defense_call(self, state, concept: C.Concept | None = None) -> tuple[str, C.Call]:
        """The call the model plays against: the computer's style call (SX.7), else its family's stand-in (no draw); its personnel matched
        to the player's play (SX.10d, Q-P13: the computer matches the offense's personnel)."""
        call_id = self.rules.books.defense_id
        call = C.BY_ID.get(call_id)
        if call is None or call.side != "D":
            call_id = DEFAULT_CALLS.get(state.defense_play, DEFAULT_CALLS[5])
            call = C.BY_ID[call_id]
        if concept is None:
            return call_id, call.params
        offense = personnel.offense_personnel(concept, state.extras.play_settings)
        return call_id, personnel.adjust(call.params, offense, to_goal(state))

    def situation(self, state, concept: C.Concept, own: bool = True) -> M.Situation:
        """The model's situation; `own`: the player's play, with his Formation and Tempo settings (the computer's play has none)."""
        settings = state.extras.play_settings if own else {}
        formation = settings.get("formation", SETTING_BOOK)
        if concept.id in OWN_FORMATION_PLAYS:
            formation = SETTING_BOOK              # SX.13: the kneel, the spike (only from under center, RB26 8-2-1 Item 3) and the throwback
        motion = settings.get("motion", SETTING_BOOK)    # (an eligible quarterback, 8-1-6) keep their own formation
        values = dict(to_goal=to_goal(state), down=state.down, distance=state.to_go,
                      formation="" if formation == SETTING_BOOK else formation,
                      motion="" if motion == SETTING_BOOK else motion,
                      protection=settings.get("protection", "normal"))
        values.update(self.ratings_door(concept))
        values.update(self.rules.choices.situation_values(state, own))      # SY.4, SY.5: the player's target and blitzer (nothing unless he chose)
        return M.Situation(**values)

    def ratings_door(self, concept: C.Concept) -> dict:
        """The Franchise's ratings (H8, design 7): a shift of the run, the completion points, the sack and fumble rates and the catch's yards,
        from the same bounded Mod the original's tables read; nothing in every other game."""
        modifiers = self.rules.modifiers
        door = getattr(modifiers, "ratings_mod", None)
        if door is None:
            return {}
        kind = "pass" if concept.kind in PASS_KINDS else "qb" if concept.kind in ("sneak", "qb_run") else "run"
        mod = door(kind)
        if mod is None:
            return {}
        base = T.FR_MODEL_FUMBLE_BASE
        return dict(run_shift=mod.ylo * 100, comp_shift=mod.comp * 100, sack_shift=mod.sack * T.FR_MODEL_SACK,
                    fumble_pct=max(10, base * 100 // max(1, base + mod.fum)), catch_yards=mod.ylo)

    def model_play(self, state):
        """After the snap sentence: the result of the called play, or None (no catalog play: the original's tables). Sets the engine's play
        number for the telling (narration_family) and gives a quarterback run its key as the branch."""
        self.result = None
        concept = C.BY_ID.get(self.called) if state.wisoff == 1 else None
        if concept is None or (concept.side != "O" and concept.id != GATE):
            return None
        call_id, call = self.defense_call(state, concept if concept.side == "O" else None)
        return self.run_model(state, concept, call_id, call)

    def computer_play(self, state):
        """SX.10e: the computer's call over the catalog (PlaybookFlow.catalog_offense) against the other side's call: the computer's own
        call over the catalog, the player's catalog call (played by the defense flow first), or the stand-in of the family the other side
        chose (no draw); its personnel matched to the play's (Q-P13). None: no such call (the original's tables)."""
        books = self.rules.books
        concept = C.BY_ID.get(books.offense_id) if books.catalog else None
        if concept is None or engine_family(concept) != state.offense_play:
            return None
        call = C.BY_ID.get(books.defense_id)
        call_id = call.id if call is not None and call.side == "D" else DEFAULT_CALLS.get(state.defense_play, DEFAULT_CALLS[5])
        played = personnel.adjust(C.BY_ID[call_id].params, concept.personnel, to_goal(state))
        return self.run_model(state, concept, call_id, played)

    def run_model(self, state, concept: C.Concept, call_id: str, call: C.Call):
        """Any offense play against any call (the player's play here, the computer's against the player's call from the defense flow): the
        model's result, the engine's play number for the telling, the events and the log; the result is kept for the end of the play."""
        own = state.wisoff == 1
        if concept.id == GATE:
            result = self.gate(state, call)
        else:
            result = M.play(concept, call, self.situation(state, concept, own), self.rules.rnd)
        if result.kind == "kneel":                  # never into the own end zone: a kneel on the own 1 loses nothing
            own = 100 - to_goal(state)
            result = result._replace(yards=max(result.yards, -(own - 1)))
        if result.gap == "qb" and result.branch != "keep":
            result = result._replace(branch=qb_key(concept))
        state.offense_play = narration_family(concept, result)
        self.rules.choices.handed_off(state, result)              # S-E1 (D-194): an RPO given to the back the player chose: he carries it
        self.result = result
        self.played = concept.id
        self.events.append((concept.id, call_id, result.kind, result.yards, result.branch))
        debuglog.event("extras", "catalog_play", play=concept.id, call=call_id, kind=result.kind, yards=result.yards,
                       branch=result.branch or None, route=result.route or None, gap=result.gap or None, side=state.wisoff)
        return result

    def gate(self, state, call: C.Call) -> M.Result:
        """The swinging gate try (K026, design 2.6): the kicking unit shifts and the snap goes to a runner; it scores when the fake kick's
        model says so (design 4.9, its distance the yards to the goal), else it is stopped short. Told as a run of the end."""
        rnd, to = self.rules.rnd, to_goal(state)
        if M.fake_kick(to, "return", rnd):
            return M.Result("run", to, gap="end")
        return M.Result("run", M.between(rnd, -2, max(-2, to - 1)), gap="end")

    def drop_result(self) -> None:
        """The engine left the model's result (a scramble, a throw-away by the grounding rule): nothing of it is used any more."""
        self.result = None

    def out_of_bounds(self, state) -> bool | None:
        """The model's out-of-bounds flag of the play being told (None: not a catalog play, the clock draws as before)."""
        return None if self.result is None else bool(self.result.out_of_bounds)

    def turnover_return(self, state):
        """The spot of an interception or a lost fumble of the catalog play (G26-8): (half, yard line, touchdown, sentence), or None (the
        original's random spot). The new offense's distance from its own goal is 100 less where the ball was caught or picked up, plus
        the return; in its own end zone it is a touch back at the 20, past the other goal line a touchdown."""
        result, self.result = self.result, None
        if result is None or result.kind not in ("interception", "fumble") or (result.kind == "fumble" and not result.fumble_lost):
            return None
        own = 100 - to_goal(state)                 # the line of scrimmage from the offense's own goal line
        where = own + result.yards                  # where the ball was caught or picked up
        new_offense = other(state.wisoff)
        player = state.rosters[state.defense].defense[state.defender1 - 1] if state.rosters.get(state.defense) else ""
        back = result.return_yards if result.kind == "interception" else 0
        position = 100 - where + back
        if result.return_touchdown or position >= 100:
            return None, None, True, X.text("NXB-H09", player=player)
        if position <= 0:
            return own_half(new_offense), 20, False, X.text("NXB-H11", player=player)
        sentence = ""
        if back > 1:
            sentence = X.text("NXB-H08", player=player, n=back)
        elif back == 1:
            sentence = X.text("NXB-H12", player=player)
        if position <= 50:
            return own_half(new_offense), position, False, sentence
        return own_half(state.wisoff), 100 - position, False, sentence

    def finish(self, state, outcome) -> None:
        """The narration end point (H2): the record names the catalog play (the clock reads it, extras/clock.py live_time), Again remembers
        the call, the menu is at its top for the next play."""
        if self.called and outcome.offense == 1 and outcome.offense_play not in (0,):
            outcome.catalog = self.called
            if C.BY_ID[self.called].side == "O":     # a kind of punt, a fake or the gate is not Again's (SX.10d)
                state.extras.again[0] = self.called
        elif self.played:                             # SX.10d, SX.10e: the computer's play the model played
            outcome.catalog = self.played
        if not (outcome.catalog and outcome.turnover):  # only the play's own turnover reads its result again (turnover_return), B-X40
            self.result = None
        self.called = self.played = ""
        self.reset()


# the W key (D-112, Q-050): what it says about a play type ("family") or a list by how the weights lie: one favourite with its chance
# (LIKELY_ONE), one play with all the weight (LIKELY_ALL), two or three or more that share the most (LIKELY_TIED), or no weight at all
# (NO_FAVOURITE: Enter takes the first play of a play type); a single play says it is one play (ONE_PLAY); every other item and a menu with
# no playbook have a sentence that says what W is for (W_FOR, W_NO_BOOK)
LIKELY_ONE, LIKELY_ALL, LIKELY_TIED = "NXB-W01", "NXB-W05", ("NXB-W02", "NXB-W03", "NXB-W04")
NO_FAVOURITE = {"family": "NXB-W06", "list": "NXB-W07"}
ONE_PLAY, W_FOR, W_NO_BOOK = "NXB-W08", "NXB-W09", "NXB-W10"


def likely_sentence(kind: str, where: str, ids, percent: int, name_of) -> str:
    """What W says about a play type ("family") or a list: the plays that share the greatest weight (`ids`) and the chance of each, in
    percent; 100 is every time; 0 means no play of it has a weight in the playbook's calling (it has no favourite). Many plays are tied
    more often than not, so a tie is told as a tie and never one of them as the favourite."""
    names = [name_of(i) for i in ids]
    if not names:
        return ""
    if percent <= 0:
        return X.text(NO_FAVOURITE[kind], list=where, name=names[0])
    if len(names) == 1:
        return X.text(LIKELY_ALL if percent >= 100 else LIKELY_ONE, list=where, name=names[0], n=percent)
    if len(names) <= 3:
        others = dict(zip(("other", "third"), names[1:]))
        return X.text(LIKELY_TIED[len(names) - 2], list=where, name=names[0], n=percent, **others)
    return X.text(LIKELY_TIED[2], list=where, name=names[0], n=percent, count=len(names))


def likely_for(flow, state, role: str, kind: str, value, family_plays, family_names, single) -> str:
    """The W sentence for one item of either side's catalog menus (OffenseFlow.likely_text, DefenseFlow.likely_text); "" when the item is
    none of: a play type, a list (opened or listed in More Plays), a play. `family_plays(family)` are the usable plays of a play type,
    `family_names` the original's names of the play types, `single` the play types that are one play each ({family: play id}). No draw."""
    menus_, books, name_of = flow.menus, flow.rules.books, flow.table.name
    group = value if kind == PM.OPEN else menus_.group if menus_.level == PM.LIST else ""
    if group in C.GROUP_BY_KEY:                                    # a list: the plays of it the playbook most likely calls
        ids, percent = books.likely(state, 1, role, PM.concepts_of(group, flow.context(state)))
        return likely_sentence("list", X.text(C.group_text_id(C.GROUP_BY_KEY[group])).strip(), ids, percent, name_of)
    if kind in (PM.CALL, PM.AGAIN):                                # one play
        return X.text(ONE_PLAY, name=name_of(value))
    if kind == PM.KICK:                                            # the original's Field Goal and Punt
        return X.text(ONE_PLAY, name=family_names[value - 1])
    if kind == PM.PICK and value in single:
        return X.text(ONE_PLAY, name=name_of(single[value]))
    if kind == PM.PICK:                                            # a play type: what Enter would most likely pick
        ids, percent = books.likely(state, 1, role, family_plays(value))
        return likely_sentence("family", family_names[value - 1], ids, percent, name_of)
    return ""


def text_for(key: str, **values) -> str:
    """The sentences of the catalog's plays that the original never had (design 7), by the engine's key (game/pag_catalog.py)."""
    return X.text(SENTENCES[key], **values)


SENTENCES = {"kneel": "NXB-H01", "spike": "NXB-H02", "throw_away": "NXB-H03", "pitch": "NXB-H04", "keep": "NXB-H05",
             "laterals": "NXB-H06", "recovered": "NXB-H07", "try_scored": "NXB-H10", "computer_try": "NXB-H16"}
