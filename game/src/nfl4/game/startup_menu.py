"""The start-up choice: what to do with what is saved. This is inspired by Jim Kitchen.

CLAUDE.md 0.23, playbook 7.17, NX-S1 to NX-S8 (D-086). The original loaded football.sav at the start, deleted it as it did, and continued a
season without a word. After the welcome, when anything is saved (a saved game in a slot, an automatic save, a season, a franchise, even a
damaged or an old one), the program says one sentence about each and asks:

    continue the saved game | choose another saved game | continue the season | continue the franchise | start a new game |
    delete the saved game | delete the season | delete the franchise | restore what was deleted

The first item is what the original did, so Enter alone does what it did. The menu is `FranchiseQuestion`, the program's own question on the
original's key wait: Up, Down, the digits, Enter, F1 (the situation again, with the help sentence of rule 0.17), F2. No path loads, deletes or
overwrites anything without one of these keys: a delete asks again (starting at no) and moves the file to the backup; a new season that would
replace a season asks first and keeps the old one in the backup; a damaged save is named and only moved by the player.

`StartupMenu.run()` returns when the player has chosen how the program goes on and leaves the answer in the Program: `saved_game` and
`load_entry` for a saved game, `new_game` ("season" or "franchise") for a new one, and the kind of season in use (`use_kind`).
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field

from ..data import debuglog
from ..data.files.shelf import Entry
from ..extras import nx_texts as X
from ..extras.franchise.question import FranchiseQuestion, ask_yes_no
from ..extras.nfl_rules import is_nfl
from . import save_summary as SS
from . import save_texts as S

log = logging.getLogger("nfl4.game")

GO, AGAIN = "go", "again"


@dataclass
class Facts:
    """What is saved right now, gathered again before every question (a delete or a restore changes it)."""
    games: list = field(default_factory=list)        # [(owner, Entry)]: every save file, whatever its state; owner "classic" or "franchise"
    season: object = None                            # a SeasonPeek of the classic season in the files, or None
    franchise: bool = False                          # a franchise that can be played is in its folder
    franchise_sentence: str = ""
    restorable: list = field(default_factory=list)   # [("game", owner) | ("season", "classic") | ("franchise", (slot, copy number))]
    franchises: list = field(default_factory=list)   # D-173: [(slot, sentence, team)] of the franchises there are, the one in use first

    @property
    def playable(self) -> list:
        return [(owner, entry) for owner, entry in self.games if entry.playable]

    @property
    def live(self) -> bool:
        return bool(self.games or self.season is not None or self.franchise)


def primary(entries: list) -> Entry | None:
    """The game the first item continues: the newest save of a slot, unless the automatic save is newer (a game that was not finished)."""
    playable = [entry for entry in entries if entry.playable]
    normal = sorted((entry for entry in playable if not entry.is_auto), key=lambda entry: -entry.stamp)
    auto = next((entry for entry in playable if entry.is_auto), None)
    if auto is not None and (not normal or auto.stamp > normal[0].stamp):
        return auto
    return normal[0] if normal else None


class StartupMenu:
    def __init__(self, program):
        self.p = program
        self.g = program.g
        self.acted = False             # a delete or a restore was done: the menu stays until the player moves on, so a restore is possible

    # ----- the stores -----

    def _franchise_store(self):
        """The store of the franchise in use (its slot): only with the N. F. L. rules (rule 0.13 / P1: Classic opens no franchise folder)."""
        if not is_nfl(self.g.rules):
            return None
        store = self.g.franchise()
        return store if store.opened and store.available else None

    def _slot_store(self, slot: int):
        """D-173: the store of franchise slot 1 to 3, opened (another slot's silently: its notices are not this start's), or None (Classic, or
        a folder that cannot be used this run)."""
        g = self.g
        if not is_nfl(g.rules):
            return None
        if slot == g.franchise_slot:
            return self._franchise_store()
        store = g.franchise_peek(slot)
        if not store.opened:
            store.open(False)
            store.take_notices()
        return store if store.available else None

    def _slots(self) -> list:
        """[(slot, store)] of the slots that can be used now (the slot in use first is not implied: 1, 2, 3)."""
        out = []
        for slot in range(1, 4):
            store = self._slot_store(slot)
            if store is not None:
                out.append((slot, store))
        return out

    def _owner(self, slot: int) -> str:
        return "franchise" if slot == self.g.franchise_slot else "franchise:%d" % slot

    def _slot_of(self, owner: str) -> int:
        return self.g.franchise_slot if owner == "franchise" else int(owner.split(":", 1)[1])

    def _stores(self) -> list:
        stores = [("classic", self.g.program_store)]
        for slot, store in self._slots():
            if store.exists:
                stores.append((self._owner(slot), store))
        return stores

    def _team(self, league) -> str:
        from ..extras.franchise.league import team_ref
        return self.g.league.team(*team_ref(league.team))

    # ----- what is saved -----

    def gather(self) -> Facts:
        g = self.g
        facts = Facts()
        for owner, store in self._stores():
            facts.games += [(owner, entry) for entry in store.shelf.scan(store.classify)]
            if store.shelf.deleted() is not None:
                facts.restorable.append(("game", owner))
        classic = self.g.program_store
        facts.season = classic.season_peek()
        if facts.season is None and classic.season_deleted():
            facts.restorable.append(("season", "classic"))
        current = g.franchise_slot
        for slot, store in sorted(self._slots(), key=lambda pair: pair[0] != current):
            if store.exists:
                facts.franchises.append((slot, self._franchise_sentence(store), self._team(store.league)))
        for slot, store in self._slots():
            for number in store.backup_numbers():
                facts.restorable.append(("franchise", (slot, number)))       # D-173: every kept copy, with a franchise in its slot or not
        if facts.franchises:
            facts.franchise = True
            facts.franchise_sentence = facts.franchises[0][1]
        return facts

    def _franchise_sentence(self, store) -> str:
        from ..extras.franchise.league import SEASON, team_ref
        from .standings import Records
        league = store.league
        team = self.g.league.team(*team_ref(league.team))
        in_season = league.stage == SEASON
        wins, losses = Records.from_file_values(league.records).record(*team_ref(league.team)) if in_season else (0, 0)
        return SS.franchise_sentence(league.coach, team, league.season, in_season, league.gtp, wins, losses, league.regular_weeks)

    def _season_sentence(self, peek) -> str:
        return SS.season_sentence(peek.coach, self.g.league.team(peek.tn1, peek.tn2), peek.gtp, peek.wins, peek.losses)

    def sentences(self, facts: Facts) -> list[str]:
        """One sentence per save, the game the first item continues first."""
        best = primary([entry for _owner, entry in facts.games])
        many = len(facts.games) > 1
        ordered = sorted(facts.games, key=lambda pair: (pair[1] is not best, not pair[1].playable, -pair[1].stamp))
        lines = [SS.game_sentence(entry, many=many and not entry.is_auto) for _owner, entry in ordered]
        if facts.season is not None:
            lines.append(self._season_sentence(facts.season))
        if len(facts.franchises) == 1:
            lines.append(facts.franchises[0][1])
        else:
            lines += [S.FRANCHISE_N % slot + sentence.lstrip() for slot, sentence, _team in facts.franchises]
        return lines

    # ----- the menu -----

    def items(self, facts: Facts) -> list:
        """[(label, action)] in the order the player hears them; the first is what the original did."""
        playable = facts.playable
        best = primary([entry for _owner, entry in playable])
        best_owner = next((owner for owner, entry in playable if entry is best), None)
        active = self.p.mode.kind
        items: list = []
        if best is not None:
            items.append((S.CONTINUE_AUTO if best.is_auto else S.CONTINUE_GAME, ("continue", best_owner, best)))
        if len(playable) > 1:
            items.append((S.CHOOSE_ANOTHER, ("choose",)))
        if len(facts.franchises) == 1:
            wants = [("franchise", S.CONTINUE_FRANCHISE, facts.franchises[0][0])]
        else:
            wants = [("franchise", S.CONTINUE_FRANCHISE_N % (slot, team), slot) for slot, _sentence, team in facts.franchises]
        wants += [("season", S.CONTINUE_SEASON, None)] if facts.season is not None else []
        wants.sort(key=lambda row: 0 if (row[0] == "franchise") == (active == "franchise") else 1)
        items += [(label, (kind, slot) if kind == "franchise" else (kind,)) for kind, label, slot in wants]
        items.append((S.NEW_GAME, ("new",)))
        if facts.games:
            items.append((S.DELETE_GAME if playable else S.DELETE_DAMAGED, ("delete_game",)))
        if facts.season is not None:
            items.append((S.DELETE_SEASON, ("delete_season",)))
        if len(facts.franchises) == 1:
            items.append((S.DELETE_FRANCHISE, ("delete_franchise", facts.franchises[0][0])))
        elif facts.franchises:
            items.append((S.DELETE_A_FRANCHISE, ("delete_franchise", None)))
        if len(facts.restorable) == 1:
            kind, owner = facts.restorable[0]
            items.append((self._restore_label(kind, owner), ("restore", kind, owner)))
        elif facts.restorable:
            items.append((S.RESTORE_SOMETHING, ("restore_which",)))
        return items

    def _restore_label(self, kind: str, owner) -> str:
        if kind == "season":
            return S.RESTORE_SEASON
        if kind == "franchise":
            slot, number = owner
            store = self._slot_store(slot)
            league = store.peek_backup(number) if store is not None else None
            if league is None:
                return S.RESTORE_FRANCHISE_UNREADABLE
            return S.RESTORE_FRANCHISE_COPY % (self._team(league), league.season)
        if owner == "franchise":
            return S.RESTORE_GAME + S.OF_THE_FRANCHISE
        if owner.startswith("franchise:"):
            return S.RESTORE_GAME + S.OF_FRANCHISE_N % self._slot_of(owner)
        return S.RESTORE_GAME

    def run(self) -> str:
        """Ask until the player moves on. Returns GO. Nothing is asked when nothing is saved (the program starts as it always did); a kept copy of a
        franchise counts as saved (D-173: a franchise deleted at one start could not be restored at the next, the menu was never shown), and so
        does every other thing the player deleted (D-176, a tester of 0.16.6: a backup must always be reachable; a deleted saved game or season
        alone never brought the menu back)."""
        while True:
            facts = self.gather()
            if not facts.live and not facts.restorable:
                return GO
            items = self.items(facts)
            situation = self.sentences(facts) + ([S.BACKUP_ONLY] if not facts.live else []) + [S.MENU_PROMPT]     # D-176
            debuglog.event("save", "startup_menu", games=[(o, e.name, e.status) for o, e in facts.games], season=facts.season is not None,
                           franchise=facts.franchise, franchises=[slot for slot, _s, _t in facts.franchises],
                           kept=[owner for kind, owner in facts.restorable if kind == "franchise"], items=[label for label, _ in items])
            answer = FranchiseQuestion(self.g, situation, [label for label, _ in items]).ask()
            action = items[answer][1]
            debuglog.event("save", "startup_choice", choice=items[answer][0])
            outcome = self._act(action, facts)
            if outcome == GO:
                return GO

    # ----- the actions -----

    def _act(self, action: tuple, facts: Facts) -> str:
        kind = action[0]
        if kind == "continue":
            return self._continue(action[1], action[2])
        if kind == "choose":
            picked = self._pick(facts.playable, S.WHICH_TO_CONTINUE, back=True)
            return self._continue(*picked) if picked is not None else AGAIN
        if kind == "season":
            self.p.use_kind("classic")
            return GO
        if kind == "franchise":
            return GO if self._use_franchise(action[1]) else AGAIN
        if kind == "new":
            return GO if self._new_game(facts) else AGAIN
        if kind == "delete_game":
            return self._delete_game(facts)
        if kind == "delete_season":
            return self._delete_season()
        if kind == "delete_franchise":
            return self._delete_franchise(action[1], facts)
        if kind == "restore":
            return self._restore(action[1], action[2])
        if kind == "restore_which":
            labels = [self._restore_label(k, o) for k, o in facts.restorable]
            answer = FranchiseQuestion(self.g, S.WHICH_TO_RESTORE, labels + [S.LIST_BACK], escape_value=-1).ask()
            if answer in (-1, len(labels)):
                return AGAIN
            return self._restore(*facts.restorable[answer])
        raise ValueError("unknown start-up action %r" % (action,))

    def _use_franchise(self, slot: int) -> bool:
        """D-173: franchise slot `slot` is put in use (the one in use before is put away first)."""
        p, g = self.p, self.g
        if slot != g.franchise_slot:
            if p.mode.kind == "franchise":
                p.use_kind("classic")
            g.select_franchise_slot(slot)
        return p.use_kind("franchise")

    def _pick(self, pairs: list, question: str, back: bool):
        """A list of saved games; the pair chosen, or None when the player goes back (Escape or the last item)."""
        labels = [SS.short_game(entry) for _owner, entry in pairs] + ([S.LIST_BACK] if back else [])
        answer = FranchiseQuestion(self.g, question, labels, escape_value=-1).ask()
        if answer == -1 or answer >= len(pairs):
            return None
        return pairs[answer]

    def _continue(self, owner: str, entry: Entry) -> str:
        p = self.p
        if owner.startswith("franchise"):
            ok = self._use_franchise(self._slot_of(owner))
        else:
            ok = p.use_kind(owner)
        if not ok:
            self.g.say2(S.COULD_NOT_RESTORE)
            return AGAIN
        p.saved_game, p.load_entry = True, entry
        debuglog.event("save", "load_chosen", file=entry.name, owner=owner, auto=entry.is_auto)
        return GO

    def _delete_game(self, facts: Facts) -> str:
        pairs = facts.games
        picked = pairs[0] if len(pairs) == 1 else self._pick(pairs, S.WHICH_TO_DELETE, back=True)
        if picked is None:
            return AGAIN
        owner, entry = picked
        store = dict(self._stores())[owner]
        if not ask_yes_no(self.g, S.DELETE_QUESTION_GAME % SS.short_game(entry), start_yes=False):
            return AGAIN
        self.g.say2(S.WAS_DELETED if store.shelf.delete(entry) else S.COULD_NOT_DELETE)
        self.acted = True
        return AGAIN

    def _delete_season(self) -> str:
        if not ask_yes_no(self.g, S.DELETE_QUESTION_SEASON, start_yes=False):
            return AGAIN
        self.g.say2(S.WAS_DELETED if self.g.program_store.delete_season() else S.COULD_NOT_DELETE)
        self.acted = True
        return AGAIN

    def _delete_franchise(self, slot, facts: Facts) -> str:
        g = self.g
        if slot is None:
            labels = ["franchise %d, the %s" % (s, team) for s, _sentence, team in facts.franchises]
            answer = FranchiseQuestion(g, S.WHICH_FRANCHISE_DELETE, labels + [S.LIST_BACK], escape_value=-1).ask()
            if answer in (-1, len(labels)):
                return AGAIN
            slot = facts.franchises[answer][0]
        store = self._slot_store(slot)
        if store is None or not store.exists:
            g.say2(S.COULD_NOT_DELETE)
            return AGAIN
        question = S.DELETE_QUESTION_FRANCHISE if len(facts.franchises) <= 1 else S.DELETE_QUESTION_FRANCHISE_N % (slot, self._team(store.league))
        if not ask_yes_no(g, question, start_yes=False):
            return AGAIN
        in_use = slot == g.franchise_slot
        if not store.delete_franchise():
            g.say2(S.COULD_NOT_DELETE)
            return AGAIN
        if in_use:
            self.p.use_kind("classic")                   # no franchise to play in this slot: the kind goes back to a classic season
        g.say2(S.WAS_DELETED)
        self.acted = True
        return AGAIN

    def _restore(self, kind: str, owner) -> str:
        g = self.g
        if kind == "season":
            if self.g.program_store.season_peek() is not None:
                g.say2(S.SEASON_EXISTS)
            else:
                g.say2(S.SEASON_RESTORED if self.g.program_store.restore_season() else S.COULD_NOT_RESTORE)
        elif kind == "franchise":
            self._restore_franchise(*owner)
        else:
            store = dict(self._stores())[owner]
            slot = store.shelf.restore()
            g.say2(S.WAS_RESTORED % slot if slot else S.EVERY_SLOT_FULL)
        self.acted = True
        return AGAIN

    def _restore_which_franchise(self, kept: list) -> None:
        """D-176: the kept copies of every franchise slot, each named by its team and season, then go back; the one chosen is restored."""
        labels = [self._restore_label("franchise", owner) for owner in kept]
        answer = FranchiseQuestion(self.g, S.WHICH_FRANCHISE_RESTORE, labels + [S.LIST_BACK], escape_value=-1).ask()
        if answer in (-1, len(labels)):
            return
        self._restore_franchise(*kept[answer])

    def _restore_franchise(self, slot: int, number: int) -> None:
        """D-173: the kept copy goes back to its own slot when that is empty, else to the first empty slot; with three franchises nothing moves."""
        g = self.g
        source = self._slot_store(slot)
        if source is None:
            g.say2(S.COULD_NOT_RESTORE)
            return
        slots = dict(self._slots())
        target_slot = slot if not source.exists else next((s for s in (1, 2, 3) if s in slots and not slots[s].exists), None)
        if target_slot is None:
            g.say2(S.EVERY_FRANCHISE_FULL)
            return
        ok = source.restore_backup(number, slots[target_slot])
        g.say2(S.FRANCHISE_RESTORED_TO % target_slot if ok else S.COULD_NOT_RESTORE)

    # ----- a new game (NX-S7) -----

    def _new_game(self, facts: Facts) -> bool:
        """The kind of new game, with the last choice first, and the one question that guards what it would replace. True: go on to the
        set-up of the kind (the program does it); False: back to the menu."""
        p, g = self.p, self.g
        kinds = [("season", S.NEW_SEASON)]
        if is_nfl(g.rules) and self._franchise_store() is not None:
            kinds.append(("franchise", S.NEW_FRANCHISE))
        kept = [owner for kind, owner in facts.restorable if kind == "franchise"]
        if kept:                                           # D-176: a deleted franchise can be brought back from the new-game question too
            kinds.append(("restore", S.RESTORE_A_FRANCHISE))
        last = 1 if g.options.settings.game.nx_season_kind == "franchise" and len(kinds) > 1 and kinds[1][0] == "franchise" else 0
        if len(kinds) > 1:
            answer = FranchiseQuestion(g, S.NEW_KIND_QUESTION, [label for _kind, label in kinds], start=last).ask()
        else:
            answer = 0
        kind = kinds[answer][0]
        if kind == "restore":
            self._restore_which_franchise(kept)
            self.acted = True
            return False
        if kind == "season":
            peek = facts.season
            if peek is not None:
                if not ask_yes_no(g, S.REPLACE_SEASON_QUESTION, start_yes=False):
                    return False
                if not g.program_store.delete_season():
                    g.say2(S.COULD_NOT_DELETE)
                    return False
                p.new_defaults = (peek.coach, peek.tn1, peek.tn2)
        else:
            slot = self._choose_slot()
            if slot is None:
                return False
            franchise = self._slot_store(slot)
            if franchise is not None and franchise.exists:
                if not ask_yes_no(g, X.text("NXF-02", team=self._team(franchise.league)), start_yes=False):
                    return False
            if slot != g.franchise_slot:
                if p.mode.kind == "franchise":
                    p.use_kind("classic")
                g.select_franchise_slot(slot)
        p.new_game = kind
        debuglog.event("save", "new_game_chosen", kind=kind, slot=g.franchise_slot if kind == "franchise" else None)
        return True

    def _choose_slot(self):
        """D-173: where the new franchise goes: the three slots, each said as empty or with its team and season; the first empty one is
        where the list starts. None: the player went back."""
        slots = dict(self._slots())
        if not slots:
            return None
        order = [s for s in (1, 2, 3) if s in slots]
        labels = []
        for s in order:
            store = slots[s]
            labels.append(S.FRANCHISE_SLOT_FULL % (s, self._team(store.league), store.league.season) if store.exists
                          else S.FRANCHISE_SLOT_EMPTY % s)
        start = next((i for i, s in enumerate(order) if not slots[s].exists), order.index(self.g.franchise_slot) if self.g.franchise_slot in order else 0)
        answer = FranchiseQuestion(self.g, S.WHICH_FRANCHISE_SLOT, labels + [S.LIST_BACK], start=start, escape_value=-1).ask()
        if answer in (-1, len(labels)):
            return None
        return order[answer]
